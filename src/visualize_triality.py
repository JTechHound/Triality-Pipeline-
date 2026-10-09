#!/usr/bin/env python3
"""
Visualize the D4 triality cycle: the three 8-dimensional representations
(8v, 8s, 8c) of Spin(8), projected from 4D to 3D, with the S3 triality
action shown on the D4 Dynkin diagram.

Left panel: 3D scatter of all 24 weights, color-coded by representation.
Right panel: D4 Dynkin diagram (central node + 3 outer nodes) with the
triality 3-cycle on the outer nodes, and the 8v -> 8c -> 8s -> 8v triangle.

[COMPUTED 2026-10-08]
"""
import itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

# ---------------------------------------------------------------- weights
e = np.eye(4)
eight_v = np.array([s * e[i] for i in range(4) for s in (1, -1)])
eight_s = np.array([np.array(v, float) / 2
                    for v in itertools.product([1, -1], repeat=4)
                    if sum(1 for x in v if x < 0) % 2 == 0])
eight_c = np.array([np.array(v, float) / 2
                    for v in itertools.product([1, -1], repeat=4)
                    if sum(1 for x in v if x < 0) % 2 == 1])
assert len(eight_v) == len(eight_s) == len(eight_c) == 8

# ------------------------------------------------- 4D -> 3D projection
# Orthogonal projection onto the hyperplane perpendicular to a generic
# direction u. (The symmetric choice u=(1,1,1,1) collapses antipodal weight
# pairs, so we use an asymmetric u and verify no collisions.)
u = np.array([0.5, 0.8, 1.3, 1.9])
u = u / np.linalg.norm(u)
basis = []
for v in [np.array([1., 0, 0, 0]), np.array([0., 1, 0, 0]),
          np.array([0., 0, 1, 0])]:
    w = v - (v @ u) * u
    for b in basis:
        w = w - (w @ b) * b
    w = w / np.linalg.norm(w)
    basis.append(w)
P = np.stack(basis)          # 3x4 projection matrix

def proj(pts):
    return (P @ pts.T).T

all4d = np.vstack([eight_v, eight_s, eight_c])
proj_pts = proj(all4d)
# verify no two weights project to the same 3D point
rounded = {tuple(np.round(p, 8)) for p in proj_pts}
assert len(rounded) == 24, "projection collision!"
print(f"projection OK: 24 distinct 3D points")

pv, ps, pc = proj(eight_v), proj(eight_s), proj(eight_c)

# ---------------------------------------------------------------- figure
C8V, C8S, C8C = "#1f77b4", "#2ca02c", "#d62728"
fig = plt.figure(figsize=(15, 6.5))

# --- left: 3D scatter ---
ax3 = fig.add_subplot(1, 2, 1, projection="3d")
ax3.scatter(pv[:, 0], pv[:, 1], pv[:, 2], s=90, c=C8V, label="8v  vector",
            depthshade=True, edgecolors="k", linewidths=0.5)
ax3.scatter(ps[:, 0], ps[:, 1], ps[:, 2], s=90, c=C8S, label="8s  spinor",
            depthshade=True, edgecolors="k", linewidths=0.5, marker="^")
ax3.scatter(pc[:, 0], pc[:, 1], pc[:, 2], s=90, c=C8C,
            label="8c  conjugate spinor", depthshade=True,
            edgecolors="k", linewidths=0.5, marker="s")
ax3.set_title("The three 8-dimensional representations of Spin(8)\n"
              "(D4 weights, projected 4D -> 3D)", fontsize=12)
ax3.legend(loc="upper left", fontsize=10)
ax3.set_axis_off()
ax3.view_init(elev=18, azim=-58)

# --- right: Dynkin diagram + triality triangle ---
ax2 = fig.add_subplot(1, 2, 2)
ax2.set_xlim(0, 10)
ax2.set_ylim(-0.6, 10)
ax2.set_aspect("equal")
ax2.axis("off")
ax2.text(5, 9.3, "D4 Dynkin diagram + triality action", fontsize=12,
         ha="center", weight="bold")

# D4: central node a2 at (5,6.5); outer a1 (2.5,8), a3 (7.5,8), a4 (5,4.5)
pos = {"a1": (2.5, 8.0), "a2": (5.0, 6.5), "a3": (7.5, 8.0), "a4": (5.0, 4.7)}
for name, (x, y) in pos.items():
    ax2.add_patch(Circle((x, y), 0.32, fc="white", ec="black", lw=1.5))
    ax2.text(x, y, name.replace("a", "α"), ha="center", va="center", fontsize=11)
for outer in ("a1", "a3", "a4"):
    x0, y0 = pos["a2"]
    x1, y1 = pos[outer]
    ax2.plot([x0, x1], [y0, y1], "k-", lw=1.5)
# S3 cycle arrows on outer nodes: a1 -> a3 -> a4 -> a1
for src, dst, col in (("a1", "a3", C8V), ("a3", "a4", C8C), ("a4", "a1", C8S)):
    x0, y0 = pos[src]
    x1, y1 = pos[dst]
    ax2.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                                  connectionstyle="arc3,rad=0.25",
                                  arrowstyle="-|>", mutation_scale=14,
                                  color=col, lw=1.6, linestyle="--",
                                  shrinkA=8, shrinkB=8))
ax2.text(5, 3.9, "S3 permutes the outer nodes: α1→α3→α4→α1", fontsize=10,
         ha="center", style="italic")

# triality triangle: 8v -> 8c -> 8s -> 8v (computed cycle order)
tri = {"8v": (2.2, 2.4), "8c": (7.8, 2.4), "8s": (5.0, 0.7)}
tcol = {"8v": C8V, "8c": C8C, "8s": C8S}
for name, (x, y) in tri.items():
    ax2.add_patch(Circle((x, y), 0.55, fc=tcol[name], ec="black", lw=1.5,
                         alpha=0.85))
    ax2.text(x, y, name, ha="center", va="center", fontsize=12,
             weight="bold", color="white")
for src, dst in (("8v", "8c"), ("8c", "8s"), ("8s", "8v")):
    x0, y0 = tri[src]
    x1, y1 = tri[dst]
    ax2.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                                  arrowstyle="-|>", mutation_scale=18,
                                  color="black", lw=2.0,
                                  shrinkA=16, shrinkB=16))
ax2.text(5, 3.1, "triality cycle  (order 3, genuinely outer)",
         fontsize=10, ha="center", style="italic")

fig.suptitle("Triality: the rigorous '3' of 3-6-9  —  S3 outer automorphism of D4",
             fontsize=14, weight="bold", y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.94])
out = "triality_cycle.png"
fig.savefig(out, dpi=150)
print(f"saved {out}")
