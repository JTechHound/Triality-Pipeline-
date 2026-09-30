"""Transmon microwave pulse sequencer (src/pulse_scheduler.py).

Module 4 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

NOTE: The source document truncated ``generate_cross_resonance_tone`` mid-signature
(``(self, duration_ns, ma``). The remainder of that method is reconstructed from the
document's outline: it builds a Gaussian-enveloped carrier tone at the target qubit
frequency, consistent with how the deployment runner consumes it.
"""

import numpy as np


class TransmonPulseScheduler:
    def __init__(self, sampling_rate_ghz=4.5, dt_ns=0.222):
        self.sampling_rate_ghz = sampling_rate_ghz
        self.dt = dt_ns * 1e-9
        self.qubit_0_freq = 4.85e9
        self.qubit_1_freq = 4.72e9

    def generate_gaussian_waveform(self, duration_ns, amplitude, sigma_ns=5.0):
        steps = int(duration_ns / (self.dt * 1e9))
        t = np.linspace(-duration_ns / 2, duration_ns / 2, steps)
        return amplitude * np.exp(-(t ** 2) / (2 * sigma_ns ** 2))

    def generate_cross_resonance_tone(self, duration_ns, main_freq_ghz, amplitude=0.5, sigma_ns=5.0):
        """Generates a cross-resonance drive tone: a Gaussian envelope modulating
        a carrier at the target qubit frequency."""
        steps = int(duration_ns / (self.dt * 1e9))
        t = np.linspace(0.0, duration_ns * 1e-9, steps)
        envelope = self.generate_gaussian_waveform(duration_ns, amplitude, sigma_ns=sigma_ns)
        carrier = np.cos(2.0 * np.pi * main_freq_ghz * 1e9 * t)
        return envelope * carrier
