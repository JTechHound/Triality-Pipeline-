"""Transmon microwave pulse sequencer (src/pulse_scheduler.py).

Module 8 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

Translates continuous machine learning weights into explicit microwave pulses.
Generates 20ns Gaussian single-qubit envelopes and 45ns flat-top
cross-resonance waves.
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

    def generate_cross_resonance_tone(self, duration_ns, max_amplitude, rise_fall_ns=4.0):
        """Generates a flat-top cross-resonance waveform with linear rise/fall edges."""
        steps = int(duration_ns / (self.dt * 1e9))
        t_array = np.linspace(0, duration_ns, steps)
        waveform = np.zeros(steps)
        for idx, t in enumerate(t_array):
            if t < rise_fall_ns:
                waveform[idx] = max_amplitude * (t / rise_fall_ns)
            elif t > (duration_ns - rise_fall_ns):
                waveform[idx] = max_amplitude * ((duration_ns - t) / rise_fall_ns)
            else:
                waveform[idx] = max_amplitude
        return waveform

    def compile_rf_schedule(self, theta, phi):
        return {
            "Control_Line_Q0_Drive_Gaussian": {
                "carrier_modulation_frequency": f"{self.qubit_0_freq / 1e9:.3f} GHz",
                "samples": len(self.generate_gaussian_waveform(20.0, 0.3 * (theta / np.pi))),
            },
            "Cross_Resonance_Line_FlatTop": {
                "carrier_modulation_frequency": f"{self.qubit_1_freq / 1e9:.3f} GHz",
                "samples": len(self.generate_cross_resonance_tone(45.0, 0.4 * (phi / np.pi))),
            },
        }
