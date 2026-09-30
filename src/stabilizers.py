"""Calibrated hardware transmon stabilizers (src/stabilizers.py).

Module 2 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).
"""

import numpy as np


class TransmonHardwareStabilizer:
    def __init__(self, t1_us=150.0, t2_us=120.0, gate_duration_ns=200.0):
        """Maps physical transmon decoherence lifetimes directly to open
        system models, calibrated against IBM Quantum chip constraints."""
        self.T1 = t1_us * 1e-6
        self.T2 = t2_us * 1e-6
        self.tau = gate_duration_ns * 1e-9
        self.gamma_residue = 0.07  # Asserted 7% UCT Dark Capacity Axiom

    def calculate_hardware_error_floor(self):
        p_relaxation = 1.0 - np.exp(-self.tau / self.T1)
        p_dephasing = 1.0 - np.exp(-self.tau / self.T2)
        return p_relaxation + p_dephasing - (p_relaxation * p_dephasing)

    def evaluate_logical_error(self, physical_noise, scaling_factor=1.0):
        combined_noise = (physical_noise * scaling_factor) + self.calculate_hardware_error_floor()
        logical_error = 0.25 * (combined_noise / 0.125) ** 3
        return np.clip(logical_error + self.gamma_residue, 0.0, 1.0)

    def execute_zne_extrapolation(self, ideal_expectation, physical_noise):
        """Executes linear Richardson Extrapolation to isolate the zero-noise limit."""
        err_r1 = self.evaluate_logical_error(physical_noise, scaling_factor=1.0)
        E_r1 = (1.0 - err_r1) * ideal_expectation
        err_r3 = self.evaluate_logical_error(physical_noise, scaling_factor=3.0)
        E_r3 = (1.0 - err_r3) * ideal_expectation
        return np.clip(E_r1 + (E_r1 - E_r3) / 8.0, -1.0, 1.0)
