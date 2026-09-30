# Triality Pipeline

Master Deployment Engine for the **Unified Triality Pipeline**
(Document Reference: UTP-SPEC-2026-V6.0).

Core Frameworks Unified: Unified Coherence Theory (UCT) × Triality Framework
× Fault-Tolerant QCNN × Multi-Terminal Hardware Routing × Empirical
Bio-Sensory Validation.

- **Release date:** September 30, 2026
- **Core authors (per source document):** Arthur Leroy Jones, u/Mikey-506, Abby Davis (Lead Research Physicist)
- **Classification:** Advanced Non-Equilibrium Open Quantum Systems Specification

## Repository structure

```
triality-pipeline/
├── master_pipeline_repository.py   # Consolidated entry point: runs the full workspace
├── master_pipeline_deployment.py   # Original deployment runner (kept working)
├── plot_confusion_matrix.py        # Presentation-grade confusion matrix graphics
├── requirements.txt
├── .gitignore
├── config/                        # Generated outputs (PNG plot, run logs, system specs)
└── src/
    ├── __init__.py
    ├── manifolds.py        # Flat-faced stargate manifolds (+ distributional rim profile)
    ├── networks.py         # High-dimensional spatial graphs, Von Neumann entropy
    ├── stabilizers.py      # Calibrated hardware transmon stabilizers
    ├── routing.py          # Integrated QCNN multi-hub router
    ├── relay_routing.py    # Dijkstra multi-hop relay around high-noise regions
    ├── routing_optimizer.py# Gradient-ascent throughput optimizer
    └── pulse_scheduler.py  # Transmon microwave pulse sequencer (flat-top CR waves)
```

## Quickstart

```bash
pip install -r requirements.txt
python3 master_pipeline_repository.py
```

The consolidated run writes `config/system_specs.json`, logs manifold validation,
synthesizes the 100-node dataset, runs the throughput optimizer, compiles the
RF pulse schedule, and saves the confusion matrix plot to
`config/confusion_matrix_plot.png`.

## Modules

- **Manifolds** — topological boundary conditions for flat-faced manifolds;
  optimized mass via Cauchy's formula (π/4 savings factor) plus the
  distributional rim line-density profile.
- **Networks** — many-body state tracking; partial-trace bipartite subspace
  extraction and Von Neumann entropy.
- **Stabilizers** — transmon decoherence (T1/T2) mapped to error floors, logical
  error evaluation, and zero-noise-limit Richardson extrapolation.
- **Routing** — 3D hub coordinates routed through shift-invariant QCNN filter
  cells, with a strict 5.0% triality thermalization barrier.
- **Relay routing** — Dijkstra multi-hop relay protocol; diverts data tracks
  around high-noise regions, assigning infinite cost to paths above the 5.0%
  noise threshold.
- **Routing optimizer** — finite-difference gradient ascent over routing weights
  to maximize global non-classical throughput.
- **Pulse scheduler** — 20ns Gaussian single-qubit envelopes, 45ns flat-top
  cross-resonance waves, and RF schedule compilation.

## Roadmap

Per the source document, candidate next milestones:

- **Readout State Discriminator** — convert raw analog IQ voltage fields back
  into classical binary bits.
- **127-qubit hardware topology routing layout** — scale the 3-hub
  cross-resonance network to a full processor matrix grid.

## Provenance note

This repository was reconstructed from three source documents
(`Master_Deployment_Engine_260930_134131_0_b95p.pdf`,
`Complete_code_block_260930_143504_2_uhzm.pdf`, and the follow-up notes text
file). All stored code as wrapped document text, so line-wrapping artifacts
were repaired and every entry point was executed end to end to validate it.
One method (`NonEquilibriumNetwork.extract_bipartite_subspace`) contained a
real indexing bug that crashed at runtime; it was corrected minimally and the
fix is marked in the code.
