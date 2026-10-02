"""Distance-3 surface-code syndrome decoder (standalone module).

[RECONSTRUCTED 2026-10-02 — referenced but never defined in any source
 document. Implemented by Lotus as an exact lookup-table MWPM over a
 verified [[9,1,3]] CSS stabilizer set, found by programmatic search.
 Verification performed:
  * every X stabilizer has even overlap with every Z stabilizer
    (they commute);
  * all 9 single-qubit X errors give distinct non-zero X syndromes;
  * all 9 single-qubit Z errors give distinct non-zero Z syndromes;
  * combined stabilizer rank is 8 (one logical qubit).
 Decoding is therefore exact for all single-qubit errors. Multi-error
 syndromes outside the table degrade gracefully (no correction applied;
 the residual is counted, not hidden).]

Ported from the UTP v5.1 spin-off (branch
COHERENCE-COLLAPSE-/-UNIFIED-TRIALITY-PIPELINE, utp-v5/pipeline_unified.py)
onto main at LJ's request, 2026-10-02.

Fills the QEC gap flagged in the FHUP Section-A audit: Section B items 31
and 40 assume distance-3 surface-code infrastructure that the pipeline
previously lacked.
"""

import numpy as np


class Distance3SurfaceCodeDecoder:
    # 3x3 data-qubit grid, row-major 0..8. X-type stabilizers detect Z
    # errors (plaquettes); Z-type stabilizers detect X errors (vertices).
    PLAQUETTE_STABILIZERS = {  # X-type -> detect Z errors
        "X1": [0, 1, 3, 4],
        "X2": [1, 2, 4, 5],
        "X3": [3, 4, 6, 7],
        "X4": [4, 5, 7, 8],
    }
    VERTEX_STABILIZERS = {  # Z-type -> detect X errors
        "Z1": [0, 1, 2],
        "Z2": [3, 4, 5],
        "Z3": [0, 3, 7, 8],
        "Z4": [1, 4, 6, 8],
    }

    def __init__(self):
        self.vertex_stabilizers = dict(self.VERTEX_STABILIZERS)
        self.plaquette_stabilizers = dict(self.PLAQUETTE_STABILIZERS)
        self.data_qubits_X_errors = np.zeros(9, dtype=int)
        self.data_qubits_Z_errors = np.zeros(9, dtype=int)
        self._x_names = list(self.vertex_stabilizers.keys())
        self._z_names = list(self.plaquette_stabilizers.keys())
        self._x_table = self._build_correction_table(self.vertex_stabilizers,
                                                    self._x_names)
        self._z_table = self._build_correction_table(self.plaquette_stabilizers,
                                                    self._z_names)

    @staticmethod
    def _build_correction_table(stabilizers, names):
        """Exact MWPM for single-qubit errors: syndrome -> correction.
        For a distance-3 code every single-qubit error has a unique
        non-zero syndrome, so the minimum-weight match is exact."""
        n = len(names)
        table = {tuple([0] * n): np.zeros(9, dtype=int)}
        for q in range(9):
            syn = tuple(1 if q in stabilizers[nm] else 0 for nm in names)
            corr = np.zeros(9, dtype=int)
            corr[q] = 1
            table.setdefault(syn, corr)
        return table

    def inject_random_phase_noise(self, noise_fraction):
        for i in range(9):
            if np.random.rand() < noise_fraction:
                self.data_qubits_Z_errors[i] ^= 1
            if np.random.rand() < (noise_fraction * 0.2):
                self.data_qubits_X_errors[i] ^= 1

    def extract_syndromes(self):
        syndrome_X = {}
        syndrome_Z = {}
        for name, qubits in self.vertex_stabilizers.items():
            syndrome_X[name] = sum(self.data_qubits_X_errors[q]
                                   for q in qubits) % 2
        for name, qubits in self.plaquette_stabilizers.items():
            syndrome_Z[name] = sum(self.data_qubits_Z_errors[q]
                                   for q in qubits) % 2
        return syndrome_X, syndrome_Z

    def minimum_weight_perfect_matching(self, syndrome):
        """Table-lookup MWPM. Unknown (multi-error) syndromes return the
        zero correction — the fault is counted downstream, not hidden."""
        if not syndrome:
            return np.zeros(9, dtype=int)
        names = self._x_names if set(syndrome) == set(self._x_names) \
            else self._z_names
        table = self._x_table if names is self._x_names else self._z_table
        key = tuple(int(syndrome[nm]) for nm in names)
        return table.get(key, np.zeros(9, dtype=int)).copy()

    def execute_active_restoration_loop(self):
        syn_X, syn_Z = self.extract_syndromes()
        correct_X = self.minimum_weight_perfect_matching(syn_X)
        correct_Z = self.minimum_weight_perfect_matching(syn_Z)
        self.data_qubits_X_errors ^= correct_X
        self.data_qubits_Z_errors ^= correct_Z
        return int(sum(self.data_qubits_X_errors) +
                   sum(self.data_qubits_Z_errors))


def _stabilizer_parity_checks():
    """Verify the [[9,1,3]] CSS set: commutation, unique single-qubit
    syndromes, combined rank 8."""
    X = Distance3SurfaceCodeDecoder.PLAQUETTE_STABILIZERS
    Z = Distance3SurfaceCodeDecoder.VERTEX_STABILIZERS
    for xn, xq in X.items():
        for zn, zq in Z.items():
            assert len(set(xq) & set(zq)) % 2 == 0, f"{xn}/{zn} anticommute"
    seen_x, seen_z = set(), set()
    for q in range(9):
        sx = tuple(1 if q in Z[nm] else 0 for nm in sorted(Z))
        sz = tuple(1 if q in X[nm] else 0 for nm in sorted(X))
        assert sx != (0,) * 4 and sx not in seen_x, f"X syndrome clash q={q}"
        assert sz != (0,) * 4 and sz not in seen_z, f"Z syndrome clash q={q}"
        seen_x.add(sx)
        seen_z.add(sz)
    rows = []
    for stab in list(X.values()) + list(Z.values()):
        row = [0] * 18
        for q in stab:
            row[q] = 1
        rows.append(row)
    assert np.linalg.matrix_rank(np.array(rows)) == 8, "rank != 8"


def run_decoder_validation(seed=0, noise_trials=200, noise_fraction=0.02):
    """Self-test: stabilizer set checks, 18/18 single-error round-trips,
    and a random-noise restoration trial. Returns True on success."""
    _stabilizer_parity_checks()
    # 18 single-qubit errors (9 X + 9 Z), each must decode to 0 residual.
    ok = 0
    for q in range(9):
        for which in ("X", "Z"):
            d = Distance3SurfaceCodeDecoder()
            if which == "X":
                d.data_qubits_X_errors[q] = 1
            else:
                d.data_qubits_Z_errors[q] = 1
            assert d.execute_active_restoration_loop() == 0, \
                f"round-trip failed q={q} {which}"
            ok += 1
    assert ok == 18
    # Random noise: mean residual should stay small at 2% noise.
    rng_residuals = []
    np.random.seed(seed)
    for _ in range(noise_trials):
        d = Distance3SurfaceCodeDecoder()
        d.inject_random_phase_noise(noise_fraction)
        rng_residuals.append(d.execute_active_restoration_loop())
    mean_res = float(np.mean(rng_residuals))
    assert mean_res < 0.5, f"noise test mean residual {mean_res}"
    print(f"decoder self-test OK: 18/18 round-trips, "
          f"noise mean residual {mean_res:.3f} "
          f"({noise_trials} trials @ {noise_fraction:.0%})")
    return True


if __name__ == "__main__":
    run_decoder_validation()
