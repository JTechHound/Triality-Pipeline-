# The Two Guards: CoherenceGuard + GoodhartGuard

**Status:** COMPUTED — `guards.py` runs clean, both guards verified in demo (2026-10-09).
**Lineage:** concepts from Mikey's *Sophia Unified Equation Stack v0.5*
(TaoishTechy/Drops); discrete implementations are new work. Mikey's E9/E140
errors do not touch these concepts.

## The idea, in one paragraph

Every self-improving system needs two watchers. The **CoherenceGuard** watches
the system itself — is the phase lock intact, or has it slipped? The
**GoodhartGuard** watches the *optimizer* — is it genuinely improving things,
or gaming the metric? Mikey's recursive theme across all his work is systems
watching themselves; these two guards are that theme made concrete and
computable.

## CoherenceGuard (Sophia E37–E48)

Watches phase-lock integrity on a ring lattice. Trips on any of:

1. **Phase deviation** (E40): max circular deviation from the mean phase
   exceeds tolerance → "coherence violation flagged."
2. **Lock erosion**: fraction of oscillators within tolerance of the mean
   drops below minimum.
3. **Winding-number change** (discrete E47, DμC = 0): on a ring, the wrapped
   phase steps must sum to 2π × integer. A phase slip changes the winding
   number — the lock is broken even if local order looks fine.

In LJ's framework this guards the phase lock — the same lock that, per the
causal-invariance work, forces a single update order and keeps the lattice
coherent. If the lock slips, there is no longer one causal history.

## GoodhartGuard (Sophia E131, E144)

*"When a measure becomes a target, it ceases to be a good measure"* — enforced
in code. Each proposed action is vetted against guard metrics with bounded
degradation rates:

```
accept ⟺ primary improved AND every guard metric within its epsilon
violation ⟹ REJECTED regardless of primary improvement
```

Guard metrics come in two flavors: `bounded_growth` (increase is bad —
fragmentation, false-reject rate) and `bounded_decline` (decrease is bad —
complexity, diversity).

## The key result: the TCI inverted-U *is* a Goodhart demonstration

The demo (Part A) runs a Kuramoto lattice under a naive optimizer that
maximizes raw synchrony R:

```
K      R      entropy   decision
0.35   0.239  3.005     baseline
0.70   0.524  2.677     ACCEPT   (healthy: R up, complexity intact)
1.40   0.938  1.674     REJECT   (gaming: R up, complexity collapses)
```

The optimizer "succeeds" — R climbs toward 1 — while destroying exactly what
coherence *is*. The TCI work (2026-10-08) measured this directly: lockstep
scores 0.87 bits/event against the 9.36 peak. The GoodhartGuard blocks the
collapse step while permitting the healthy one. Without the guard, any
self-optimizing system in the framework will optimize its coherence metric
into the ground and call it success.

## Demo (Part B): the coherence guard

- Tightly locked lattice (R = 1.000): guard passes, winding = 0.
- One full 2π twist injected around the ring: winding 0 → 1, guard trips —
  `winding number 1 != reference 0 (phase slip: D_mu C != 0)`.

## Honest limitations

- The per-step guard can be crept past by many tiny degrading steps
  (gradient-style gaming). Cumulative tracking is the natural extension.
- The coherence guard's tolerances are set for near-perfect locks; a noisy
  real lattice needs calibrated thresholds, not 0.05 rad.
- These are watchers, not fixers: they flag and reject, they don't repair.
  Repair policy belongs to the system designer (LJ).
