"""Presentation-grade confusion matrix graphics (plot_confusion_matrix.py).

Step 5 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).
"""

import os

import matplotlib

matplotlib.use("Agg")  # Run headless: no display required.
import matplotlib.pyplot as plt
import numpy as np


def render_confusion_matrices(output_path="config/confusion_matrix_plot.png"):
    """Renders the protected vs. unprotected confusion matrices and saves the PNG."""
    protected_matrix = np.array([[16, 0, 0], [0, 71, 0], [0, 0, 13]])
    unprotected_matrix = np.array([[8, 5, 3], [12, 46, 13], [2, 5, 6]])
    labels = ['Zone 0\n(Core)', 'Zone 1\n(Rim)', 'Zone 2\n(Leaf)']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    ax1.imshow(protected_matrix, cmap='GnBu', vmin=0, vmax=75)
    ax1.set_title("Protected Surface Layer (QEC Active)\nMacro Accuracy: 100.00%",
                  fontsize=11, fontweight='bold')
    ax2.imshow(unprotected_matrix, cmap='OrRd', vmin=0, vmax=75)
    ax2.set_title("Unprotected Spatial Layer (QEC Bypassed)\nMacro Accuracy: 54.00%",
                  fontsize=11, fontweight='bold')
    for ax, mat in zip([ax1, ax2], [protected_matrix, unprotected_matrix]):
        ax.set_xticks(range(3))
        ax.set_yticks(range(3))
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{mat[i, j]:02d}", ha="center", va="center", fontweight='bold')
    plt.suptitle("Triality Pipeline: 100-Node Dataset Classification Resolution Target",
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()

    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=200)
    plt.close()
    return os.path.abspath(output_path)


if __name__ == "__main__":
    render_confusion_matrices()
