# Unified Triality Pipeline — Master Compilation Engine v5.1

Single-file production build (`pipeline_unified.py`) of the UTP SPEC-2026-V5.0
system: MPS tensor engine, MPO long-range gates, Lindblad leaf dissipation,
distance-3 surface-code decoder, MOGOPS filter optimizer, three-zone softmax
classifier, TDA homology layer, geodesic discord router, fail-closed
dual-stream proof-block parser, async SQUID queue (VISA + mock), and the Adam
triadic gradient optimizer — plus a 4-test integrity harness.

## Provenance

Assembled 2026-10-02 by Lotus from four source documents (base spec, upgrade
patch, v5.1 re-synthesis, v5_2 patch). The v5.1/v5_2 headers claimed all 15
audit items were resolved; every claim was verified against the code and
several were false (decoder still undefined, MPO transpose missing, minus
signs "fixed" only in comments, seeding claimed but absent). This file applies
the real fixes. See the REPAIR LOG in the module docstring.

Two components are reconstructions (marked `[RECONSTRUCTED]` inline), because
no source document contained them:

- **Distance-3 surface-code decoder** — exact lookup-table MWPM over a
  `[[9,1,3]]` CSS stabilizer set that was verified programmatically
  (commutation, unique single-qubit syndromes, rank 8). Exact for single-qubit
  errors; multi-error syndromes degrade gracefully (counted, not hidden).
- **Peripheral-leaf Lindblad engine** — only the `__init__` signature existed;
  the body is a standard exact dephasing-channel step.

## Deliberate placeholders

- `SIGMA_THRESHOLD = 0.053` — global tunable; the FHUP audit flags this exact
  value as an unestimated free parameter.
- `GAMMA_RESIDUE = 0.07257 = ln(1/0.93)` — derived from the 0.93 monogamy
  bound, not free.

## Validation (2026-10-02)

- MPS init / memory footprint: harness Test 1.
- MPO chain vs direct Rzz application: fidelity 1.0 (the sources' version
  missed by 1.449 in operator norm / silently contracted wrong legs).
- Decoder round-trip: all 18 single-qubit X/Z errors decode to zero residual.
- Lindblad step: trace-preserving.
- Proof block: harness passes with `entropy_leak_source=0.07` bound against
  the membrane metric (non-vacuous); fails closed on mismatch.
- Full harness (`python pipeline_unified.py`): writes `metrics.json` +
  `series.csv`, exit 0.

## Run

```
pip install -r requirements.txt
python pipeline_unified.py
```

`use_mock_hardware=False` enables the real VISA path (requires `pyvisa` and an
instrument); any VISA failure falls back to the mock path with a loud warning.
