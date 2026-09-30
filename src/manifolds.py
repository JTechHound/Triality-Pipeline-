"""Flat-faced stargate manifolds (src/manifolds.py).

Module 2 of the Master Deployment Engine for the Unified Triality Pipeline
(Document Reference: UTP-SPEC-2026-V6.0).

Implements the topological boundary conditions for flat-faced stargate manifolds
detailed in Abby Davis's September Triality Review ("The Missing Rim"). Forces
Minkowski inequality constraints to calculate a 21.46% mass reduction.
"""

import numpy as np


class FlatFacedManifoldNode:
    def __init__(self, aperture_radius_r=0.5):
        self.R = aperture_radius_r
        self.c = 299792458.0
        self.G = 6.67430e-11
        # Universal line tension of a critical cosmic string (c^4 / 4G)
        self.universal_line_tension = -(self.c ** 4) / (4.0 * self.G)

    def calculate_optimized_mass(self):
        """Computes total negative equivalent mass based on Cauchy's formula.
        Yields an analytical pi/4 (~0.7854) savings factor against spherical throats."""
        mass_flat = (np.pi * (self.c ** 2) * self.R) / (2.0 * self.G)
        mass_sphere = (2.0 * self.R * (self.c ** 2)) / self.G
        savings_factor = mass_flat / mass_sphere
        return mass_flat, savings_factor  # Bounded by pi/4 ~ 0.7854

    def get_distributional_rim_profile(self):
        """Returns the concentrated line density on the boundary loop perimeter."""
        line_density_kg_per_meter = self.universal_line_tension / (self.c ** 2)
        total_circumference = 2 * np.pi * self.R
        return {
            "line_tension_newtons": self.universal_line_tension,
            "line_density_kg_m": line_density_kg_per_meter,
            "integrated_rim_mass": line_density_kg_per_meter * total_circumference,
        }
