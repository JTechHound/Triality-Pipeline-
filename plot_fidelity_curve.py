"""Quantum state fidelity vs phase noise chart (plot_fidelity_curve.py).

Sections 2.2 & 1.2 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

Plots the protected dual-layer pipeline fidelity (QEC fault knee at 12.5%)
against the unprotected layer's sigmoidal collapse past the 5.0% raw noise
threshold down to the dark capacity residue floor (~0.00014 bits).
"""

import os

import matplotlib

matplotlib.use("Agg")  # Run headless: no display required.
import matplotlib.pyplot as plt
import numpy as np


def render_fidelity_curve(output_path="config/triality_fidelity_curve.png"):
    """Renders the fidelity-vs-noise chart and saves the PNG."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # 1. Define Phase Noise Fraction Domain (0% to 16%)
    sigma = np.linspace(0, 0.16, 500)

    # 2. Model the Unprotected Layer Sigmoidal Collapse (Threshold at 5.0%).
    # Drops sharply past 5.0% down to the dark capacity residue floor (~0.00014 bits).
    beta_unprotected = 85
    sigma_th_unprotected = 0.05
    F_unprotected = 1.0 / (1.0 + np.exp(beta_unprotected * (sigma - sigma_th_unprotected)))
    F_unprotected = np.clip(F_unprotected * (1.0 - 0.15 * (sigma / 0.05) ** 2), 0.00014, 1.0)
    F_unprotected[sigma > 0.075] = 0.00014

    # 3. Model the Protected Dual-Layer Pipeline (Fault Knee at 12.5%)
    beta_protected = 95
    sigma_th_protected = 0.125
    F_protected = 1.0 / (1.0 + np.exp(beta_protected * (sigma - sigma_th_protected)))
    F_protected = np.clip(F_protected, 0.00014, 1.0)

    # 4. Generate the Modern Technical Chart
    fig, ax = plt.subplots(figsize=(8.5, 5), facecolor='#0B0F19')
    ax.set_facecolor('#0B0F19')

    # Plot curves with neon styling appropriate for a quantum pipeline
    ax.plot(sigma * 100, F_protected, color='#00FFCC',
            label='Protected Dual-Layer Pipeline', linewidth=2.5)
    ax.plot(sigma * 100, F_unprotected, color='#FF3366',
            label='Unprotected Layer', linewidth=2.5, linestyle='--')

    # Trace critical threshold markers from the framework
    ax.axvline(x=5.0, color='#FF3366', linestyle=':', alpha=0.6, linewidth=1.5)
    ax.text(5.2, 0.15, 'Raw Noise Threshold\n' r'($\sigma = 5.0\%$)',
            color='#FF3366', fontsize=9, fontweight='bold')

    ax.axvline(x=12.5, color='#00FFCC', linestyle=':', alpha=0.6, linewidth=1.5)
    ax.text(12.7, 0.65, 'QEC Fault Knee\n' r'($\sigma \approx 12.5\%$)',
            color='#00FFCC', fontsize=9, fontweight='bold')

    # Chart formatting & typography
    ax.set_title('The Unified Triality Pipeline: Quantum State Fidelity vs Phase Noise',
                 color='white', fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel('Physical Phase Noise Fraction ' r'($\sigma$, %)',
                  color='#A0AABF', fontsize=10)
    ax.set_ylabel('Quantum State Fidelity (F)', color='#A0AABF', fontsize=10)
    ax.set_xlim(0, 16)
    ax.set_ylim(-0.05, 1.05)
    ax.tick_params(colors='#A0AABF', labelsize=9)
    ax.grid(color='#1E293B', linestyle='-', linewidth=0.5)

    # Style Legend
    leg = ax.legend(loc='upper right', frameon=True,
                    facecolor='#1E293B', edgecolor='#334155')
    for text in leg.get_texts():
        text.set_color('white')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Fidelity curve saved to '{output_path}'.")


if __name__ == "__main__":
    render_fidelity_curve()
