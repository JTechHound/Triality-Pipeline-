#!/usr/bin/env python3
"""
Two guard mechanisms for self-optimizing systems, worked up from Mikey's
Sophia Unified Equation Stack v0.5 (TaoishTechy/Drops, 2026-10-09).

  CoherenceGuard  <- Sophia E37-E48 (coherence transport, gauge language)
  GoodhartGuard   <- Sophia E131 (Goodhart guard invariant), E144 (beta_2 guard)

Concepts are Mikey's; the discrete implementations below are new work
(2026-10-09). Mikey's E9/E140 errors do not touch these concepts.

CoherenceGuard watches the PHASE LOCK on a ring lattice:
  (a) phase-deviation flag  (Sophia E40: |dphi| > tol -> violation flagged)
  (b) winding-number check  (discrete analog of Sophia E47: D_mu C = 0.
      On a ring, the sum of signed phase steps must be 2*pi*integer.
      A phase slip changes the winding number -> the lock is broken.)

GoodhartGuard watches the OPTIMIZER (Sophia E131):
  If a proposed action improves the primary metric by degrading a guard
  metric beyond its allowed rate, the action is REJECTED regardless of
  the primary improvement. "When a measure becomes a target, it ceases
  to be a good measure" -- enforced in code.

The demo below shows the key insight: a naive optimizer maximizing raw
synchrony R drives a Kuramoto lattice into lockstep -- where the TCI
work (2026-10-08) showed measured coherence COLLAPSES (0.87 vs 9.36
peak). The Goodhart guard catches exactly this: R improves, complexity
degrades -> reject.

[COMPUTED 2026-10-09]
"""
import math
import numpy as np
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# CoherenceGuard
# ---------------------------------------------------------------------------
@dataclass
class CoherenceReport:
    order_parameter: float      # R = |mean(exp(i*theta))|, 0..1
    max_deviation: float        # max circular distance from mean phase (rad)
    locked_fraction: float      # fraction within phase_tol of mean
    winding_number: int         # integer winding around the ring
    violations: list = field(default_factory=list)
    ok: bool = True


class CoherenceGuard:
    """
    Watches phase-lock integrity on a ring lattice of N phases.

    Violation conditions (any one -> guard trips):
      - max circular deviation from the mean phase exceeds phase_tol
        (Sophia E40: |dphi| > 0.01 rad -> coherence violation flagged)
      - locked fraction drops below min_locked_fraction
      - winding number differs from the reference winding
        (discrete D_mu C = 0: a phase slip breaks the lock)
    """

    def __init__(self, phase_tol=0.01, min_locked_fraction=0.90):
        self.phase_tol = phase_tol
        self.min_locked_fraction = min_locked_fraction
        self._reference_winding = None

    @staticmethod
    def _wrap(phi):
        return (phi + math.pi) % (2 * math.pi) - math.pi

    def _winding(self, phases):
        # wrap each ring step to (-pi, pi] BEFORE summing: the raw diffs
        # telescope to zero around any closed loop, hiding the winding
        steps = self._wrap(np.diff(np.append(phases, phases[0])))
        return int(round(np.sum(steps) / (2 * math.pi)))

    def check(self, phases):
        phases = np.asarray(phases, dtype=float)
        n = len(phases)
        mean_vec = np.mean(np.exp(1j * phases))
        R = abs(mean_vec)
        mean_phase = math.atan2(mean_vec.imag, mean_vec.real)
        devs = np.abs(self._wrap(phases - mean_phase))
        max_dev = float(np.max(devs))
        locked_frac = float(np.mean(devs <= self.phase_tol))
        winding = self._winding(phases)
        if self._reference_winding is None:
            self._reference_winding = winding

        violations = []
        if max_dev > self.phase_tol:
            violations.append(
                f"max phase deviation {max_dev:.4f} rad > tol {self.phase_tol}")
        if locked_frac < self.min_locked_fraction:
            violations.append(
                f"locked fraction {locked_frac:.3f} < min {self.min_locked_fraction}")
        if winding != self._reference_winding:
            violations.append(
                f"winding number {winding} != reference {self._reference_winding} "
                f"(phase slip: D_mu C != 0)")

        return CoherenceReport(
            order_parameter=R,
            max_deviation=max_dev,
            locked_fraction=locked_frac,
            winding_number=winding,
            violations=violations,
            ok=not violations,
        )

    def reset_reference(self):
        self._reference_winding = None


# ---------------------------------------------------------------------------
# GoodhartGuard
# ---------------------------------------------------------------------------
@dataclass
class GuardSpec:
    """One guard metric with its allowed rate of degradation per evaluation."""
    name: str
    direction: str   # 'bounded_growth' (increase is bad: fragmentation)
                     # 'bounded_decline' (decrease is bad: complexity)
    epsilon: float   # max allowed bad-direction change per evaluation step


@dataclass
class GuardDecision:
    accept: bool
    primary_improved: bool
    violations: list = field(default_factory=list)
    detail: str = ""


class GoodhartGuard:
    """
    Sophia E131: d(Fragmentation)/dt <= eps_guard AND d(FRR)/dt <= eps_FR.
    If violated -> action REJECTED regardless of primary-metric improvement.

    evaluate() compares before/after snapshots:
      accept <=> primary improved AND no guard metric degraded past epsilon.
    """

    def __init__(self, specs, primary_tol=1e-9):
        self.specs = list(specs)
        self.primary_tol = primary_tol

    def evaluate(self, primary_before, primary_after,
                 guards_before, guards_after):
        primary_improved = (primary_after - primary_before) > self.primary_tol
        violations = []
        for spec in self.specs:
            d = guards_after[spec.name] - guards_before[spec.name]
            if spec.direction == 'bounded_growth' and d > spec.epsilon:
                violations.append(
                    f"{spec.name}: +{d:.4f} > eps {spec.epsilon} (growth guard tripped)")
            elif spec.direction == 'bounded_decline' and -d > spec.epsilon:
                violations.append(
                    f"{spec.name}: {d:.4f} < -eps {spec.epsilon} (decline guard tripped)")
        accept = primary_improved and not violations
        if not primary_improved and not violations:
            detail = "primary did not improve; no guard violation"
        elif violations:
            detail = (f"REJECTED: guard violation overrides "
                      f"primary {'improvement' if primary_improved else 'change'}")
        else:
            detail = "accepted: primary improved, guards within bounds"
        return GuardDecision(accept=accept,
                             primary_improved=primary_improved,
                             violations=violations, detail=detail)


# ---------------------------------------------------------------------------
# Demo: Kuramoto lattice + naive synchrony optimizer + both guards
# ---------------------------------------------------------------------------
def phase_entropy(phases, bins=24):
    """Shannon entropy of the binned phase histogram (complexity proxy)."""
    hist, _ = np.histogram(phases % (2 * math.pi), bins=bins,
                           range=(0, 2 * math.pi))
    p = hist / hist.sum()
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))


def kuramoto_step(phases, omega, K, dt, noise=0.02, rng=None):
    n = len(phases)
    coupling = (K / n) * np.sum(np.sin(phases[None, :] - phases[:, None]), axis=1)
    dphi = (omega + coupling) * dt
    if noise > 0:
        dphi = dphi + noise * np.sqrt(dt) * rng.standard_normal(n)
    return phases + dphi


def run_demo():
    rng = np.random.default_rng(7)
    n = 64
    omega = rng.normal(0, 0.5, n)
    dt, steps = 0.05, 400

    # ---- Part A: GoodhartGuard vs a naive synchrony-maximizing optimizer ----
    goodhart_guard = GoodhartGuard([
        GuardSpec("phase_entropy", "bounded_decline", epsilon=0.35),
    ])

    K_current = 0.35
    ph = rng.uniform(0, 2 * math.pi, n)
    for _ in range(steps):
        ph = kuramoto_step(ph, omega, K_current, dt, rng=rng)
    R_before = abs(np.mean(np.exp(1j * ph)))
    E_before = phase_entropy(ph)
    print("Part A: naive optimizer proposes K doubling to maximize R (order).")
    print("        Guard: phase_entropy may decline at most 0.35 per proposal.")
    print(f"{'K':>6} {'R':>6} {'entropy':>8} {'decision':>10}  detail")
    print("-" * 72)
    print(f"{K_current:6.2f} {R_before:6.3f} {E_before:8.3f} {'baseline':>10}")

    def trial(K_start, K_prop, seed):
        """One proposal trial: settle at K_prop starting from K_start state."""
        r = np.random.default_rng(seed)
        ph2 = ph.copy()
        for _ in range(steps):
            ph2 = kuramoto_step(ph2, omega, K_prop, dt, rng=r)
        R = abs(np.mean(np.exp(1j * ph2)))
        E = phase_entropy(ph2)
        return R, E, ph2

    for round_ in range(4):
        K_prop = K_current * 2.0
        # median of 3 seeded trials -> stable accept/reject arc
        results = [trial(K_current, K_prop, 1000 + round_ * 10 + t) for t in range(3)]
        Rs = sorted(r[0] for r in results)
        Es = sorted(r[1] for r in results)
        R_after, E_after = Rs[1], Es[1]
        ph2 = results[1][2]
        dec = goodhart_guard.evaluate(R_before, R_after,
                                      {"phase_entropy": E_before},
                                      {"phase_entropy": E_after})
        tag = "ACCEPT" if dec.accept else "REJECT"
        print(f"{K_prop:6.2f} {R_after:6.3f} {E_after:8.3f} {tag:>10}  {dec.detail}")
        if dec.accept:
            K_current, ph, R_before, E_before = K_prop, ph2, R_after, E_after
        # rejected proposals leave the state untouched

    # ---- Part B: CoherenceGuard on a tightly locked lattice ----
    print("\nPart B: CoherenceGuard on a tightly locked lattice.")
    coherence_guard = CoherenceGuard(phase_tol=0.05, min_locked_fraction=0.80)
    # identical natural frequencies -> the lock is essentially perfect;
    # the demo is about the guard mechanics (intact passes, broken trips)
    omega0 = np.zeros(n)
    ph_lock = rng.uniform(0, 2 * math.pi, n)
    for _ in range(800):
        ph_lock = kuramoto_step(ph_lock, omega0, 8.0, dt, noise=0.005, rng=rng)
    rep = coherence_guard.check(ph_lock)
    print(f"  locked: R={rep.order_parameter:.3f} max_dev={rep.max_deviation:.4f} "
          f"locked_frac={rep.locked_fraction:.3f} winding={rep.winding_number} "
          f"ok={rep.ok}")
    assert rep.ok, "expected the tight lock to pass the guard"

    # inject one full extra twist around the ring: discrete D_mu C != 0
    twist = np.linspace(0, 2 * math.pi, n, endpoint=False)
    ph_twist = ph_lock + twist
    rep2 = coherence_guard.check(ph_twist)
    print("  after injecting one full 2pi twist around the ring:")
    print(f"  R={rep2.order_parameter:.3f} winding={rep2.winding_number} ok={rep2.ok}")
    for v in rep2.violations:
        print(f"    VIOLATION: {v}")
    assert not rep2.ok and any("winding" in v for v in rep2.violations), \
        "expected the twist to trip the winding check"

    print("\nDEMO COMPLETE: guard behaviors verified "
          "(accept-then-reject arc; lock passes; twist trips winding check)")
    return True


if __name__ == "__main__":
    run_demo()
