#!/usr/bin/env python3
"""
master_pipeline_deployment.py
================================================================
Document Reference: UTP-SPEC-2026-V6.0
Release Date: September 30, 2026
Core Authors: Arthur Leroy Jones, u/Mikey-506, Abby Davis
Classification: Advanced Non-Equilibrium Open Quantum Systems Specification
================================================================
Consolidated Master Deployment Engine for the Unified Triality Pipeline.
Integrates Flat-Faced Manifolds, 3D Networks, Transmon Noise Maps,
QCNN Multi-Hub Routing, and Automated Performance Matrix Profiling.

NOTE: Reconstructed from the source document. The document's code block was
truncated in the middle of this runner (steps between the pulse scheduler and
the graphics engine); those sections were rebuilt from the document's outline
(input data logging, transmon wave profiles, control-line reporting) and the
whole script was validated by executing it end to end.
"""

import json
import os

import matplotlib

matplotlib.use("Agg")  # Run headless: no display required.
import matplotlib.pyplot as plt  # noqa: F401  (kept for parity with the source document)
import numpy as np  # noqa: F401  (kept for parity with the source document)

from plot_confusion_matrix import render_confusion_matrices
from src.manifolds import FlatFacedManifoldNode
from src.pulse_scheduler import TransmonPulseScheduler
from src.routing import QCNNMultiHubRouter
from src.stabilizers import TransmonHardwareStabilizer

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(REPO_ROOT, "config")


def execute_master_workspace_run():
    os.makedirs(CONFIG_DIR, exist_ok=True)

    print("=" * 64)
    print("  MASTER PIPELINE DEPLOYMENT - UNIFIED TRIALITY PIPELINE")
    print("  Document Reference: UTP-SPEC-2026-V6.0")
    print("=" * 64)

    # 1. Input data logging - manifold boundary conditions.
    print("\n[Input Data] Logging manifold boundary conditions...")
    manifold = FlatFacedManifoldNode(aperture_radius_r=0.5)
    mass_flat, mass_ratio = manifold.calculate_optimized_mass()
    print(f" |- Aperture radius R: {manifold.R} m")
    print(f" |- Universal line tension: {manifold.universal_line_tension:.4e} N")
    print(f" |- Optimized mass (flat): {mass_flat:.4e} kg"
          f" | flat/sphere ratio: {mass_ratio:.4f} (bounded by pi/4 ~ 0.7854)")

    # 2. Transmon hardware stabilizer - noise map calibration.
    print("\n[Stabilizer] Calibrating transmon noise map...")
    stabilizer = TransmonHardwareStabilizer(t1_us=150.0, t2_us=120.0, gate_duration_ns=200.0)
    error_floor = stabilizer.calculate_hardware_error_floor()
    print(" |- T1: 150.0 us | T2: 120.0 us | gate duration: 200.0 ns")
    print(f" |- Hardware error floor: {error_floor:.6f}")

    run_log = {
        "document_reference": "UTP-SPEC-2026-V6.0",
        "manifold": {
            "aperture_radius_r": manifold.R,
            "mass_flat_kg": mass_flat,
            "mass_ratio_flat_over_sphere": mass_ratio,
        },
        "stabilizer": {
            "t1_us": 150.0,
            "t2_us": 120.0,
            "gate_duration_ns": 200.0,
            "hardware_error_floor": error_floor,
        },
    }
    with open(os.path.join(CONFIG_DIR, "run_log.json"), "w") as fh:
        json.dump(run_log, fh, indent=2)
    print(" |- Run log written to config/run_log.json")

    # 3. Pulse scheduler - transmon hardware wave profiles.
    print("\n[Pulse Scheduler] Generating transmon hardware wave profiles...")
    scheduler = TransmonPulseScheduler(sampling_rate_ghz=4.5, dt_ns=0.222)
    traces = [
        ("Q0 Drive", scheduler.qubit_0_freq / 1e9, "gaussian"),
        ("Q1 Drive", scheduler.qubit_1_freq / 1e9, "gaussian"),
        ("Q0<->Q1 Cross-Resonance", scheduler.qubit_1_freq / 1e9, "cross_resonance"),
    ]
    for trace, carrier_freq_ghz, kind in traces:
        if kind == "cross_resonance":
            waveform = scheduler.generate_cross_resonance_tone(160.0, max_amplitude=0.4)
        else:
            waveform = scheduler.generate_gaussian_waveform(40.0, amplitude=0.5)
        config = {"carrier_freq_ghz": carrier_freq_ghz, "samples_count": len(waveform)}
        print(f" |- Control Line: {trace} | Carrier Modulation: {config['carrier_freq_ghz']:.2f} GHz"
              f" | Width: {config['samples_count']} DAC Samples")

    # 4. QCNN multi-hub routing - compressed network channels.
    print("\n[QCNN Router] Routing compressed network channels...")
    hubs = {
        "Hub-A": (0.0, 0.0, 0.0),
        "Hub-B": (1.0, 0.5, 0.2),
        "Hub-C": (0.3, 1.0, 0.6),
    }
    router = QCNNMultiHubRouter(hubs, lambda_scale=0.7)
    channels = router.route_compressed_network_channels(physical_noise=0.02)
    for channel, capacity in channels.items():
        print(f" |- {channel}: {capacity:.6f}")

    # 5. Render presentation matrix graphics (plot_confusion_matrix.py).
    print("\n[Graphics Engine] Exporting Macro-Scale Confusion Matrix Plots...")
    plot_path = render_confusion_matrices(os.path.join(CONFIG_DIR, "confusion_matrix_plot.png"))
    print(f"[Graphics Engine] Presentation PNG Exported Natively to"
          f" '{os.path.relpath(plot_path, REPO_ROOT)}'")

    print("\n" + "=" * 64)
    print("  MASTER PIPELINE RUN COMPLETE: ALL CONFIG MATRIX FILTERS ACTIVE")
    print("=" * 64)


if __name__ == "__main__":
    execute_master_workspace_run()
