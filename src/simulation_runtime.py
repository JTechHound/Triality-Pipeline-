"""Classical qudit simulation runtime (src/simulation_runtime.py).

Implements the "Classical Qudit Simulation Runtime" specification
(items 1-30 of the FHUP Enhancement Protocol, message-2_7_jxbf.txt):
memory bounds, backend selection, Weyl-Heisenberg operators,
statevector / MPS evolution, Lindblad open-system dynamics, fidelity and
truncation metrics, capacity planning with kill tests, and an SVD ablation
framework.

Backends CPU_SPARSE_PAULI and CPU_STABILIZER are declared in the Backend
enum per the spec but raise NotImplementedError: they are not implemented
in this revision (no silently-wrong fallback).
"""

import math
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


# ---------------------------------------------------------------------------
# Spec item 28 helper: golden ratio used for phi-weighted SVD thresholds.
# ---------------------------------------------------------------------------
PHI = (1.0 + math.sqrt(5.0)) / 2.0

COMPLEX128_BYTES = 16


class CapacityExceeded(MemoryError):
    """Raised by capacity_kill_test when a (ansatz, d, n, chi) config
    exceeds the RAM budget (spec item 30)."""


# ---------------------------------------------------------------------------
# Spec items 1-8: memory bounds and capacity formulas.
# ---------------------------------------------------------------------------
def statevector_bytes(d, n):
    """Spec item 1: M = 16 * d**N bytes for a complex128 statevector."""
    return COMPLEX128_BYTES * (d ** n)


def max_qudits(ram_bytes, d):
    """Spec items 2-4: largest N with 16 * d**N <= ram_bytes."""
    return int(math.floor(math.log(ram_bytes / COMPLEX128_BYTES) / math.log(d)))


def mps_bytes(n, d, chi):
    """Spec item 5: M ~= 16 * n * d * chi**2 bytes for an MPS."""
    return COMPLEX128_BYTES * n * d * chi ** 2


def chi_exact(n, d):
    """Spec item 6: bond dimension for an exact MPS representation."""
    return d ** (n // 2)


def chi_max(ram_bytes, n, d):
    """Spec item 7: largest chi with 16 * n * d * chi**2 <= ram_bytes."""
    return int(math.floor(math.sqrt(ram_bytes / (COMPLEX128_BYTES * n * d))))


def density_matrix_bytes(d, n):
    """Spec item 8: M = 16 * d**(2N) bytes for a dense density matrix."""
    return COMPLEX128_BYTES * (d ** (2 * n))


def effective_qudits(n, d):
    """Spec item 9: effective qudits = number of logical tensor factors,
    not the total Hilbert-space dimension."""
    return int(n)


# ---------------------------------------------------------------------------
# Spec items 10-12: backend enum, domain extension, QuditSpec.
# ---------------------------------------------------------------------------
class Backend(Enum):
    """Spec item 10: execution backend selector."""
    CPU_STATEVECTOR = "cpu_statevector"
    CPU_MPS = "cpu_mps"
    CPU_SPARSE_PAULI = "cpu_sparse_pauli"   # declared; not implemented
    CPU_STABILIZER = "cpu_stabilizer"       # declared; not implemented
    MMAP_TENSOR = "mmap_tensor"


# Spec item 11: domain extension tag for simulation-layer qudit objects.
SIM_QUDIT = "SIM_QUDIT"


@dataclass
class QuditSpec:
    """Spec item 12: declarative simulation specification."""
    n: int
    d: int = 2
    ansatz: str = "statevector"  # "statevector" | "mps" | "density_matrix"
    chi: int = 0                 # MPS bond cap (0 = exact)
    dtype: object = np.complex128
    seed: int = 0
    provenance: str = ""
    domain: str = SIM_QUDIT


# ---------------------------------------------------------------------------
# Spec items 13-17: Weyl-Heisenberg operators and their action.
# ---------------------------------------------------------------------------
def weyl_clock(d):
    """Spec item 13: Z|j> = omega**j |j>, omega = exp(2*pi*i/d)."""
    omega = np.exp(2j * np.pi / d)
    return np.diag(omega ** np.arange(d)).astype(np.complex128)


def weyl_shift(d):
    """Spec item 14: X|j> = |(j+1) mod d>."""
    X = np.zeros((d, d), dtype=np.complex128)
    for j in range(d):
        X[(j + 1) % d, j] = 1.0
    return X


def check_weyl_algebra(d):
    """Spec item 15: verify ZX = omega * XZ; returns Frobenius residual."""
    Z, X = weyl_clock(d), weyl_shift(d)
    omega = np.exp(2j * np.pi / d)
    return float(np.linalg.norm(Z @ X - omega * (X @ Z)))


def _apply_single_qudit_op(psi, op, n, d, target):
    """Apply a d x d operator to one qudit of a statevector."""
    psi_t = psi.reshape([d] * n)
    psi_t = np.moveaxis(psi_t, target, 0)
    psi_t = (op @ psi_t.reshape(d, -1)).reshape([d] + [d] * (n - 1))
    return np.moveaxis(psi_t, 0, target).reshape(-1)


def apply_clock(psi, n, d, target):
    """Spec item 16: multiply phases along the selected qudit axis."""
    return _apply_single_qudit_op(psi, weyl_clock(d), n, d, target)


def apply_shift(psi, n, d, target):
    """Spec item 17: roll the statevector along the selected qudit axis."""
    return _apply_single_qudit_op(psi, weyl_shift(d), n, d, target)


def apply_two_qudit_gate(psi, gate, n, d, i, j):
    """Spec item 18: two-qudit gate on a statevector via tensordot.

    gate is (d**2, d**2) acting on qudits (i, j); contraction order is
    (i, j) -> rows index d*i_out + j_out.
    """
    psi_t = psi.reshape([d] * n)
    psi_t = np.moveaxis(psi_t, (i, j), (0, 1))
    rest = psi_t.reshape(d * d, -1)
    out = gate @ rest
    out = out.reshape([d, d] + [d] * (n - 2))
    out = np.moveaxis(out, (0, 1), (i, j))
    return out.reshape(-1)


# ---------------------------------------------------------------------------
# Spec items 19-20: matrix-product-state evolution and SVD compression.
# Open-boundary MPS; core k has shape (chi_left, d, chi_right).
# ---------------------------------------------------------------------------
class MPS:
    """Minimal MPS supporting two-site gates (spec item 19) and SVD
    compression with discarded-weight accounting (spec item 20)."""

    def __init__(self, cores, chi_cap=0):
        self.cores = cores
        self.n = len(cores)
        self.d = cores[0].shape[1]
        self.chi_cap = chi_cap  # 0 = no cap
        self.discarded_weight = 0.0

    @classmethod
    def from_statevector(cls, psi, n, d, chi_cap=0, seed=0):
        """Successive SVD splits; optionally truncate to chi_cap."""
        mps = cls._exact(psi, n, d)
        mps.chi_cap = chi_cap
        if chi_cap:
            mps.compress(chi_cap)
        return mps

    @classmethod
    def _exact(cls, psi, n, d):
        obj = cls.__new__(cls)
        obj.n, obj.d, obj.chi_cap = n, d, 0
        obj.discarded_weight = 0.0
        rest = psi.reshape(d, -1)
        cores = []
        chi_left = 1
        for k in range(n - 1):
            u, s, vh = np.linalg.svd(rest, full_matrices=False)
            chi = s.shape[0]
            cores.append(u.reshape(chi_left, d, chi))
            obj.discarded_weight += 0.0
            rest = (np.diag(s) @ vh).reshape(chi * d, -1)
            chi_left = chi
        cores.append(rest.reshape(chi_left, d, 1))
        obj.cores = cores
        return obj

    def bond_dims(self):
        return [c.shape[0] for c in self.cores[1:]]

    def to_statevector(self):
        psi = self.cores[0]
        for core in self.cores[1:]:
            psi = np.tensordot(psi, core, axes=([-1], [0]))
            # merge: (..., d_k, chi) x (chi, d_{k+1}, chi') -> (..., d_k, d_{k+1}, chi')
            s = psi.shape
            psi = psi.reshape(s[:-3] + (s[-3] * s[-2], s[-1]))
        return psi.reshape(-1)

    def _truncate(self, s):
        """Truncate a singular-value spectrum to chi_cap; accumulate the
        discarded weight (spec item 20: return discarded weight)."""
        if self.chi_cap and s.shape[0] > self.chi_cap:
            discarded = float(np.sum(s[self.chi_cap:] ** 2))
            self.discarded_weight += discarded
            return s[:self.chi_cap], discarded
        return s, 0.0

    def two_site_gate(self, gate, i):
        """Spec item 19: fuse cores i,i+1, contract the gate, split via SVD."""
        a, b = self.cores[i], self.cores[i + 1]
        chil, d, chim = a.shape
        _, _, chir = b.shape
        theta = np.tensordot(a, b, axes=([2], [0]))          # (chil, d, d, chir)
        theta = theta.transpose(0, 3, 1, 2).reshape(chil * chir, d * d)
        # gate acts as (d*d, d*d) on the (i, j) pair, row-major in d
        theta = (gate @ theta.T).T.reshape(chil, chir, d, d)
        theta = theta.transpose(0, 2, 3, 1).reshape(chil * d, d * chir)
        u, s, vh = np.linalg.svd(theta, full_matrices=False)
        s, _ = self._truncate(s)
        chi = s.shape[0]
        self.cores[i] = u[:, :chi].reshape(chil, d, chi)
        self.cores[i + 1] = (np.diag(s) @ vh[:chi, :]).reshape(chi, d, chir)

    def compress(self, chi_new):
        """Spec item 20: right-to-left truncation sweep. Each bond's
        Schmidt spectrum is read from the SVD of the current
        orthogonality-center core, truncated to chi_new, and the
        discarded weight is accumulated. Returns the newly discarded
        weight."""
        old_cap = self.chi_cap
        self.chi_cap = chi_new
        total_before = self.discarded_weight
        for i in range(self.n - 2, -1, -1):
            # core i+1 is the orthogonality center: its SVD yields the
            # true Schmidt values of bond i (left part is an isometry,
            # right part is right-canonical by the sweep invariant).
            c = self.cores[i + 1]
            chil, d, chir = c.shape
            u, s, vh = np.linalg.svd(c.reshape(chil, d * chir),
                                     full_matrices=False)
            s, _ = self._truncate(s)
            chi = s.shape[0]
            # right-canonical core from vh
            self.cores[i + 1] = vh[:chi, :].reshape(chi, d, chir)
            # absorb u @ diag(s) into the left neighbor (new center)
            a = self.cores[i]
            al = a.shape[0]
            center = a.reshape(al * d, chil) @ (u[:, :chi] * s)
            self.cores[i] = center.reshape(al, d, chi)
        self.chi_cap = old_cap
        return self.discarded_weight - total_before


# ---------------------------------------------------------------------------
# Spec items 21-22: Lindblad open-system dynamics.
# ---------------------------------------------------------------------------
def lindblad_rhs(rho, H, Ls):
    """Spec item 21: drho/dt = -i[H, rho] + sum_k L_k rho L_k^dag
    - 1/2 {L_k^dag L_k, rho}."""
    out = -1j * (H @ rho - rho @ H)
    for L in Ls:
        LdL = L.conj().T @ L
        out += L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
    return out


def lindblad_rk4_step(rho, H, Ls, dt):
    """Spec item 22: four-stage Runge-Kutta update for the density matrix."""
    k1 = lindblad_rhs(rho, H, Ls)
    k2 = lindblad_rhs(rho + 0.5 * dt * k1, H, Ls)
    k3 = lindblad_rhs(rho + 0.5 * dt * k2, H, Ls)
    k4 = lindblad_rhs(rho + dt * k3, H, Ls)
    out = rho + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    # re-hermitize against floating-point drift
    return 0.5 * (out + out.conj().T)


# ---------------------------------------------------------------------------
# Spec item 23: zero-copy disk-backed tensor view.
# ---------------------------------------------------------------------------
class MMapTensorView:
    """Zero-copy disk-backed complex array via np.memmap (spec item 23).
    Usable as a context manager; the backing file is removed on exit."""

    def __init__(self, shape, dtype=np.complex128):
        self._file = tempfile.NamedTemporaryFile(delete=False, suffix=".mmap")
        self._file.close()
        self.path = self._file.name
        self.array = np.memmap(self.path, dtype=dtype, mode="w+", shape=shape)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try:
            del self.array
        finally:
            if os.path.exists(self.path):
                os.remove(self.path)
        return False


# ---------------------------------------------------------------------------
# Spec items 24-26: fidelity, truncation error, efficiency metric.
# ---------------------------------------------------------------------------
def state_fidelity(psi_exact, psi_approx):
    """Spec item 24: F = |<psi_exact|psi_approx>|^2."""
    overlap = np.vdot(psi_exact, psi_approx)
    return float(np.abs(overlap) ** 2)


def truncation_error(singvals):
    """Spec item 25: epsilon_trunc = 1 - sum_k lambda_k^2
    (singular values assumed normalized)."""
    return float(1.0 - np.sum(np.asarray(singvals, dtype=float) ** 2))


@dataclass
class EfficiencyTracker:
    """Spec item 26: Xi = useful_flops /
    (flops + memcpy + compress + decode).

    All counters are abstract cost units; the caller must use consistent
    units (the spec mixes flops with byte/object counts, so no physical
    unit is assumed here).
    """
    useful_flops: float = 0.0
    overhead_flops: float = 0.0
    memcpy: float = 0.0
    compress: float = 0.0
    decode: float = 0.0

    def xi(self):
        denom = (self.useful_flops + self.overhead_flops + self.memcpy
                 + self.compress + self.decode)
        if denom <= 0:
            return 0.0
        return self.useful_flops / denom


# ---------------------------------------------------------------------------
# Spec items 27-28: ablation framework and phi-weighted SVD threshold.
# ---------------------------------------------------------------------------
def phi_weighted_truncate(singvals, cutoff):
    """Spec item 28: weight singular values by S_k / PHI**rank(k)
    (rank 0 = largest) and keep those above cutoff. Returns the kept
    singular values and the discarded weight."""
    s = np.asarray(sorted(singvals, reverse=True), dtype=float)
    weights = s / (PHI ** np.arange(s.shape[0]))
    keep = weights > cutoff
    kept = s[keep]
    discarded = float(np.sum(s[~keep] ** 2))
    return kept, discarded


def svd_ablation(singvals, chi_values=(32, 64, 128, 256),
                 policies=("plain", "phi")):
    """Spec item 27: compare chi in {32,64,128,256} against two SVD
    truncation policies. Returns {policy: {chi: discarded_weight}}.

    'plain' keeps the top-chi values; 'phi' keeps values whose
    phi-weighted score clears the same relative cutoff.
    """
    s = np.asarray(sorted(singvals, reverse=True), dtype=float)
    total = float(np.sum(s ** 2))
    results = {}
    for policy in policies:
        per_chi = {}
        for chi in chi_values:
            if policy == "plain":
                kept = s[:chi]
                per_chi[chi] = float(total - np.sum(kept ** 2))
            elif policy == "phi":
                if chi >= s.shape[0]:
                    per_chi[chi] = 0.0
                else:
                    cutoff = s[chi - 1] / (PHI ** (chi - 1))
                    _, discarded = phi_weighted_truncate(s, cutoff)
                    per_chi[chi] = discarded
            else:
                raise ValueError(f"unknown policy {policy!r}")
        results[policy] = per_chi
    return results


# ---------------------------------------------------------------------------
# Spec items 29-30: capacity card and capacity kill test.
# ---------------------------------------------------------------------------
def capacity_card(spec, ram_budget_bytes):
    """Spec item 29: RAM formulas for every ansatz under one spec."""
    n, d, chi = spec.n, spec.d, spec.chi or chi_exact(spec.n, spec.d)
    return {
        "statevector": statevector_bytes(d, n),
        "mps": mps_bytes(n, d, chi),
        "density_matrix": density_matrix_bytes(d, n),
        "ram_budget": ram_budget_bytes,
        "chi_exact": chi_exact(n, d),
        "chi_max_for_budget": chi_max(ram_budget_bytes, n, d),
        "max_qudits_for_budget": max_qudits(ram_budget_bytes, d),
    }


def capacity_kill_test(spec, ram_budget_bytes):
    """Spec item 30: refuse any (ansatz, d, n, chi) whose RAM formula
    exceeds budget. Returns the chosen Backend or raises CapacityExceeded."""
    card = capacity_card(spec, ram_budget_bytes)
    if spec.ansatz == "statevector":
        need = card["statevector"]
        backend = Backend.CPU_STATEVECTOR
    elif spec.ansatz == "mps":
        need = card["mps"]
        backend = Backend.CPU_MPS
    elif spec.ansatz == "density_matrix":
        need = card["density_matrix"]
        backend = Backend.CPU_STATEVECTOR  # dense rho lives on CPU
    elif spec.ansatz in ("sparse_pauli", "stabilizer"):
        raise NotImplementedError(
            f"backend for ansatz {spec.ansatz!r} is declared but not implemented")
    else:
        raise ValueError(f"unknown ansatz {spec.ansatz!r}")
    if need > ram_budget_bytes:
        raise CapacityExceeded(
            f"{spec.ansatz} n={spec.n} d={spec.d} chi={spec.chi} needs "
            f"{need} bytes > budget {ram_budget_bytes}")
    return backend
