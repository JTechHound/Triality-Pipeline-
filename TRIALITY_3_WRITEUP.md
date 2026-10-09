# The "3" of 3-6-9, Made Explicit: D4 Triality

**Status:** COMPUTED — `triality_automorphism.py` passes all checks (2026-10-08).
**Author block:** per LJ's standing author block.

## Claim

The "3" in 3-6-9 is not numerology. It is the **S₃ outer automorphism group of D₄**
— triality — acting on the three 8-dimensional representations of Spin(8):

- **8v** — vector: weights ±eᵢ (the "position/matter" phase)
- **8s** — spinor: weights (±½,±½,±½,±½), even parity (the "spinor/coherence" phase)
- **8c** — conjugate spinor: weights (±½,±½,±½,±½), odd parity (the "conjugate/response" phase)

The triality map σ cycles them: **8v → 8c → 8s → 8v**, order 3. The three phases
are not three separate things — they are one structure seen under the outer
automorphism. That is what "triality" means, rigorously.

## What was computed

1. **24 D₄ roots** = the 24-cell vertices (permutations of (±1,±1,0,0)). Confirmed: 24 roots.
2. **Weyl group W(D₄)** = even signed permutations, order **192**. Confirmed.
3. **Three 8-weight sets**, each generated as the Weyl orbit of a minuscule
   fundamental weight (ω₁, ω₃, ω₄ — the three outer nodes of the D₄ Dynkin diagram).
   Each orbit has exactly 8 weights; cross-checked against closed forms.
4. **Triality σ**: defined by the 3-cycle on outer simple roots
   (α₁→α₃→α₄→α₁, α₂ fixed). σ is **orthogonal, order 3, half-integral** —
   it genuinely mixes coordinates, which is why it cannot be seen inside SO(8).
5. **Outerness**: every element of W(D₄) is an integral matrix; σ is half-integral,
   so σ ∉ W(D₄). The automorphism is genuinely outer — confirmed both by the
   integrality argument and by explicit comparison against all 192 Weyl elements.
6. **The cycle**: σ permutes the three 8-sets as a single 3-cycle. Confirmed.

## The F₄ connection (bonus, computed)

⟨W(D₄), σ⟩ has order 192 × 6 = **1152 = |W(F₄)|**. The S₃ triality is exactly what
promotes D₄'s symmetry to F₄'s — the same 1152-element group in the propagator
isotropy test (`24cell-propagator/`). The 24-cell's full symmetry *is* D₄ plus triality.

## Framework reading

- The three phases of the triad are the three 8-dimensional representations.
  Triality permuting them is the mathematical content of "3."
- The "9" is **not derived here** — the rigorous statement stops at the 3.
  The 9-axis structure remains as previously posed (conjecture); this write-up
  does not claim to ground it.
- **Observation, not a claim:** |S₃| = 6. The framework's 6-phase flux is
  independently grounded (6 octahedral cells per 24-cell vertex); whether the
  S₃ order is the same 6 or a coincidence is an open question, flagged for LJ.

## What this replaces

Any hand-waving about "3-ness." From here on, when the framework says "3,"
it points here: the outer automorphism group of D₄, computed and verified.
Lisi's E₈ wreckage (Distler–Garibaldi) is avoided because no claim is made that
E₈ yields the Standard Model — the triality automorphism is used as structure,
not as particle physics.
