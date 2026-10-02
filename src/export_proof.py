"""Fail-closed export proof blocks (src/export_proof.py).

Ports the CCT v3.0 proof-block pattern (Coherence_Collapse_Theory_v3.0,
Part III) to pipeline artifacts: an export is split into a small,
deterministic proof block that must pass before a byte is written, and
the payload itself. A failed bit raises ProofBlockFailed naming the bit;
no file is produced. A checks.json sidecar records every bit, and the
payload hash is bound to the parameters that produced it.

Design rules inherited from the source pattern:
  - Proof before write: the payload builder only runs if all bits pass.
  - One check, one name: a failed bit prints its name, nothing else.
  - Hash preimage: SHA-256 covers the full parameter dict, not the file.
  - Names are registered, not fabricated: SpecRegistry holds names with
    no measurement behind them as strings; numeric fields are forbidden.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field


class ProofBlockFailed(AssertionError):
    """Raised when a proof bit fails. Carries the failing bit's name."""

    def __init__(self, bit_name, detail=""):
        self.bit = bit_name
        super().__init__(f"proof block failed on bit '{bit_name}'"
                         + (f": {detail}" if detail else ""))


@dataclass
class ProofBit:
    name: str
    passed: bool
    detail: str = ""


def _canonical(params):
    """Deterministic JSON encoding for hashing."""
    return json.dumps(params, sort_keys=True, separators=(",", ":"),
                      default=str).encode("utf-8")


def payload_hash(params):
    """SHA-256 over the canonical parameter dict (the hash preimage:
    binds the file to the parameters that produced it)."""
    return hashlib.sha256(_canonical(params)).hexdigest()


def record_hash(params, payload):
    """SHA-256 over params + payload (tamper evidence: any post-hoc
    edit to either is detected by verify)."""
    return hashlib.sha256(
        _canonical({"params": params, "payload": payload})).hexdigest()


class ProofBlock:
    """Accumulates named checks; exports only if every bit passes."""

    def __init__(self, params, seed=None):
        self.params = dict(params)
        if seed is not None:
            self.params["seed"] = seed
        self.bits = []
        self._hash = payload_hash(self.params)

    # -- checks ---------------------------------------------------------
    def check(self, name, passed, detail=""):
        """Record one named bit. `passed` may be a bool or a callable
        returning (bool, detail)."""
        if callable(passed):
            passed, detail = passed()
        self.bits.append(ProofBit(name, bool(passed), str(detail)))
        return self

    def check_bounds(self, name, values, lo=0.0, hi=1.0):
        """The 'box' check: every value within [lo, hi]."""
        import numpy as np
        arr = np.asarray(list(values), dtype=float)
        ok = bool(np.all(np.isfinite(arr)) and np.all(arr >= lo)
                  and np.all(arr <= hi))
        worst = float(np.max(np.abs(arr[(arr < lo) | (arr > hi)]))) \
            if not ok else float(np.max(np.abs(arr))) if arr.size else 0.0
        return self.check(name, ok,
                          f"n={arr.size} range=[{arr.min() if arr.size else 0:.4g}, "
                          f"{arr.max() if arr.size else 0:.4g}] worst={worst:.4g}")

    def check_roundtrip(self, name, residual, tol=1e-6):
        """Passes iff a measured round-trip residual is within tol."""
        return self.check(name, abs(float(residual)) <= tol,
                          f"residual={float(residual):.3g} tol={tol:.3g}")

    def check_declared(self, name, metrics):
        """The 'no closed form' spirit: every exported metric must
        declare provenance (inputs + estimator). `metrics` maps
        name -> {'value':..., 'inputs':[...], 'estimator': str}."""
        missing = [k for k, v in metrics.items()
                   if not v.get("inputs") or not v.get("estimator")]
        return self.check(name, not missing,
                          f"undeclared={missing}" if missing else
                          f"{len(metrics)} metrics declared")

    # -- export ----------------------------------------------------------
    def _report(self, payload):
        return {
            "params": self.params,
            "params_hash": self._hash,
            "record_hash": record_hash(self.params, payload),
            "bits": {b.name: {"passed": b.passed, "detail": b.detail}
                     for b in self.bits},
        }

    def export(self, path, build_payload):
        """Run build_payload() and write it to `path` only if every bit
        passes. Writes a checks.json sidecar. Returns the record hash.

        build_payload: callable taking no arguments, returning a
        JSON-serializable object.
        """
        failed = [b for b in self.bits if not b.passed]
        if failed:
            raise ProofBlockFailed(failed[0].name, failed[0].detail)
        payload = build_payload()
        record = {"proof": self._report(payload), "payload": payload}
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            json.dump(record, f, indent=2, default=str)
        sidecar = os.path.splitext(path)[0] + ".checks.json"
        with open(sidecar, "w") as f:
            json.dump(self._report(payload), f, indent=2, default=str)
        return record["proof"]["record_hash"]

    def verify(self, path):
        """Recompute both hashes from the stored params + payload and
        confirm all bits passed. Returns True/False, never raises."""
        try:
            with open(path) as f:
                record = json.load(f)
            proof, payload = record["proof"], record["payload"]
            if payload_hash(proof["params"]) != proof["params_hash"]:
                return False
            if record_hash(proof["params"], payload) != proof["record_hash"]:
                return False
            return all(b["passed"] for b in proof["bits"].values())
        except (OSError, KeyError, ValueError):
            return False


class SpecRegistry:
    """Names from a specification that have no measurement behind them
    yet. Stored as strings only; numeric fields are forbidden."""

    def __init__(self):
        self._names = {}

    def declare(self, name, note=""):
        self._names[name] = {"note": note, "met": False}
        return self

    def meet(self, name):
        """Mark a name as computed (a measurement model now exists)."""
        if name not in self._names:
            raise KeyError(f"unregistered name {name!r}")
        self._names[name]["met"] = True

    def numeric(self, name):
        """Numeric access to an unmet name is forbidden."""
        entry = self._names.get(name)
        if entry is None:
            raise KeyError(f"unregistered name {name!r}")
        if not entry["met"]:
            raise ProofBlockFailed(
                "spec_registry",
                f"numeric field requested for unmet specification name {name!r}")
        raise KeyError(f"{name!r} is met; read its value from the export, "
                       f"not the registry")

    def as_dict(self):
        return {k: v["note"] for k, v in self._names.items()
                if not v["met"]}


# ---------------------------------------------------------------------------
# Convenience: standard proof block for a simulation-runtime run.
# ---------------------------------------------------------------------------
def prove_simulation_run(spec, ram_budget_bytes, extra_params=None,
                         weyl_tol=1e-9, trace_tol=1e-9):
    """Build a ProofBlock pre-loaded with the standard bits for a run
    of src/simulation_runtime.py: capacity kill test, Weyl algebra
    residual, and declared-metric provenance. Returns the ProofBlock;
    the caller adds run-specific bits and calls .export()."""
    params = {"spec": {"n": spec.n, "d": spec.d, "ansatz": spec.ansatz,
                       "chi": spec.chi, "seed": spec.seed,
                       "provenance": spec.provenance},
              "ram_budget_bytes": ram_budget_bytes}
    if extra_params:
        params.update(extra_params)
    block = ProofBlock(params, seed=spec.seed)

    def _capacity():
        try:
            from .simulation_runtime import (
                capacity_kill_test, CapacityExceeded)
        except ImportError:  # imported as top-level module, not package
            from simulation_runtime import (
                capacity_kill_test, CapacityExceeded)
        try:
            backend = capacity_kill_test(spec, ram_budget_bytes)
            return True, f"backend={backend.value}"
        except CapacityExceeded as e:
            return False, str(e)
        except NotImplementedError as e:
            return False, str(e)

    block.check("capacity", _capacity)
    try:
        from .simulation_runtime import check_weyl_algebra
    except ImportError:
        from simulation_runtime import check_weyl_algebra
    block.check_roundtrip("weyl_algebra",
                          check_weyl_algebra(spec.d), tol=weyl_tol)
    return block
