"""
Generate realistic mock data for the fiber microstructure dashboard.
Run this script once to populate the data/ directory.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

MATERIALS = ["Nylon", "Carbone", "Verre", "Cuivre", "PET recyclé", "Chanvre"]
BATCHES = ["LOT-A", "LOT-B", "LOT-C"]
DILATION_TYPES = ["longitudinal", "isotropic"]
N_DIRECTIONS_OPTIONS = [13, 25, 37, 49, 61]
ISSUE_TYPES = ["artifact", "low_contrast", "incomplete_volume", "segmentation_error",
               "oversized_object", "noise", "ok"]
SEVERITIES = ["low", "medium", "high"]

MATERIAL_DIAMETER = {
    "Nylon": (15, 3),
    "Carbone": (7, 1.5),
    "Verre": (10, 2),
    "Cuivre": (20, 4),
    "PET recyclé": (25, 6),
    "Chanvre": (30, 8),
}

MATERIAL_LENGTH = {
    "Nylon": (800, 150),
    "Carbone": (1200, 200),
    "Verre": (1000, 180),
    "Cuivre": (600, 100),
    "PET recyclé": (700, 130),
    "Chanvre": (2000, 400),
}


def make_sample_ids(n):
    return [f"S{i:03d}" for i in range(1, n + 1)]


def generate_samples():
    n = rng.integers(25, 41)
    ids = make_sample_ids(n)
    materials = rng.choice(MATERIALS, size=n)
    batches = rng.choice(BATCHES, size=n)

    resolution = rng.uniform(1, 20, size=n).round(2)
    voxel_size = (resolution * rng.uniform(0.9, 1.1, size=n)).round(3)
    volume = rng.uniform(0.5, 10, size=n).round(3)
    porosity = rng.uniform(0.40, 0.95, size=n).round(3)
    fiber_count = rng.integers(50, 3001, size=n)
    contact_count = (fiber_count * rng.uniform(0.8, 3.5, size=n)).astype(int)
    contact_density = (contact_count / volume).round(2)

    mean_diameters = np.array([rng.normal(MATERIAL_DIAMETER[m][0], MATERIAL_DIAMETER[m][1]) for m in materials]).clip(2, 80).round(2)
    std_diameters = (mean_diameters * rng.uniform(0.1, 0.3, size=n)).round(2)
    mean_lengths = np.array([rng.normal(MATERIAL_LENGTH[m][0], MATERIAL_LENGTH[m][1]) for m in materials]).clip(100, 5000).round(1)
    std_lengths = (mean_lengths * rng.uniform(0.1, 0.35, size=n)).round(1)
    mean_curvature = rng.uniform(0.001, 0.05, size=n).round(4)
    orientation_dispersion = rng.uniform(5, 60, size=n).round(2)
    misorientation_threshold = rng.choice([2, 4, 6, 8, 10, 12, 14, 16, 18, 20], size=n).astype(float)
    n_directions = rng.choice(N_DIRECTIONS_OPTIONS, size=n)
    dilation_type = rng.choice(DILATION_TYPES, size=n)
    slenderness_ratio = (mean_lengths / mean_diameters).round(2)
    runtime_sec = (fiber_count * rng.uniform(0.05, 0.3, size=n) + n_directions * rng.uniform(10, 40, size=n)).round(1)
    quality_score = rng.choice([1, 2, 3, 4, 5], size=n, p=[0.05, 0.10, 0.20, 0.35, 0.30])

    base_date = datetime(2025, 1, 15)
    processing_dates = [base_date + timedelta(days=int(rng.integers(0, 300))) for _ in range(n)]
    processing_dates_str = [d.strftime("%Y-%m-%d") for d in processing_dates]

    statuses = rng.choice(["completed", "completed", "completed", "in_progress", "failed"], size=n)

    notes_pool = [
        "High quality scan", "Slight edge artifacts", "Re-processed after calibration",
        "Manual quality check passed", "Automatic pipeline", "Resolution below optimal",
        "Fiber bundle detected, split manually", "", "", "", "",
    ]
    notes = [random.choice(notes_pool) for _ in range(n)]

    df = pd.DataFrame({
        "sample_id": ids,
        "material": materials,
        "batch": batches,
        "resolution_um": resolution,
        "voxel_size": voxel_size,
        "volume_mm3": volume,
        "porosity": porosity,
        "fiber_count": fiber_count,
        "contact_count": contact_count,
        "contact_density": contact_density,
        "mean_diameter_um": mean_diameters,
        "std_diameter_um": std_diameters,
        "mean_length_um": mean_lengths,
        "std_length_um": std_lengths,
        "mean_curvature": mean_curvature,
        "orientation_dispersion": orientation_dispersion,
        "misorientation_threshold": misorientation_threshold,
        "n_directions": n_directions,
        "dilation_type": dilation_type,
        "slenderness_ratio": slenderness_ratio,
        "runtime_sec": runtime_sec,
        "quality_score": quality_score,
        "processing_date": processing_dates_str,
        "status": statuses,
        "notes": notes,
    })
    return df


def generate_fibers(samples_df):
    rows = []
    fiber_id_counter = 1
    target_total = 5000
    n_samples = len(samples_df)
    fibers_per_sample = max(1, target_total // n_samples)

    for _, sample in samples_df.iterrows():
        sid = sample["sample_id"]
        material = sample["material"]
        mean_d, std_d = MATERIAL_DIAMETER[material]
        mean_l, std_l = MATERIAL_LENGTH[material]
        actual_count = min(int(sample["fiber_count"]), fibers_per_sample + rng.integers(-20, 21))
        actual_count = max(10, actual_count)

        for _ in range(actual_count):
            diameter = float(rng.normal(mean_d, std_d))
            diameter = max(1.0, diameter)
            length = float(rng.normal(mean_l, std_l))
            length = max(diameter * 2, length)
            theta = float(rng.uniform(0, 90))
            psi = float(rng.uniform(0, 360))
            curvature = float(rng.exponential(0.01))
            n_contacts = int(rng.poisson(2.5))
            contact_area = float(rng.exponential(50)) if n_contacts > 0 else 0.0
            volume_voxels = int((np.pi * (diameter / 2) ** 2 * length) / (sample["voxel_size"] ** 3) * rng.uniform(0.8, 1.2))
            rows.append({
                "fiber_id": f"F{fiber_id_counter:06d}",
                "sample_id": sid,
                "diameter_um": round(diameter, 2),
                "length_um": round(length, 1),
                "orientation_theta": round(theta, 2),
                "orientation_psi": round(psi, 2),
                "curvature": round(curvature, 5),
                "n_contacts": n_contacts,
                "mean_contact_area_um2": round(contact_area, 2),
                "volume_voxels": volume_voxels,
            })
            fiber_id_counter += 1

    return pd.DataFrame(rows)


def generate_contacts(fibers_df, target=3000):
    rows = []
    contact_id = 1
    samples = fibers_df["sample_id"].unique()

    for sid in samples:
        sample_fibers = fibers_df[fibers_df["sample_id"] == sid]["fiber_id"].tolist()
        if len(sample_fibers) < 2:
            continue
        n_contacts = max(1, int(target * len(sample_fibers) / len(fibers_df)))
        for _ in range(n_contacts):
            f1, f2 = rng.choice(sample_fibers, size=2, replace=False)
            rows.append({
                "contact_id": f"C{contact_id:06d}",
                "sample_id": sid,
                "fiber_id_1": f1,
                "fiber_id_2": f2,
                "contact_area_um2": round(float(rng.exponential(80)), 2),
                "angle_between_fibers": round(float(rng.uniform(5, 90)), 2),
            })
            contact_id += 1

    return pd.DataFrame(rows)


def generate_parameter_sweep(samples_df):
    sweep_samples = samples_df.sample(4, random_state=SEED)["sample_id"].tolist()
    thresholds = list(range(2, 22, 2))
    rows = []
    sweep_id = 1

    for sid in sweep_samples:
        base_row = samples_df[samples_df["sample_id"] == sid].iloc[0]
        base_fibers = base_row["fiber_count"]
        base_contacts = base_row["contact_count"]
        base_diameter = base_row["mean_diameter_um"]
        base_length = base_row["mean_length_um"]

        for threshold in thresholds:
            for n_dir in N_DIRECTIONS_OPTIONS:
                for dil in DILATION_TYPES:
                    noise_factor = rng.uniform(0.95, 1.05)
                    fiber_count = int(base_fibers * (0.7 + 0.03 * threshold) * noise_factor)
                    contact_count = int(base_contacts * (0.6 + 0.04 * threshold) * noise_factor)
                    orphan_fraction = max(0, 0.15 - 0.01 * threshold + rng.normal(0, 0.02))
                    runtime = float(base_row["runtime_sec"] * (n_dir / 37) * rng.uniform(0.9, 1.1))
                    mean_d = base_diameter * (1 + rng.uniform(-0.05, 0.05))
                    mean_l = base_length * (1 + rng.uniform(-0.08, 0.08))
                    rows.append({
                        "sweep_id": f"SW{sweep_id:05d}",
                        "sample_id": sid,
                        "misorientation_threshold": threshold,
                        "n_directions": n_dir,
                        "dilation_type": dil,
                        "fiber_count": max(10, fiber_count),
                        "contact_count": max(0, contact_count),
                        "orphan_fraction": round(float(orphan_fraction), 4),
                        "runtime_sec": round(runtime, 1),
                        "mean_diameter_um": round(float(mean_d), 2),
                        "mean_length_um": round(float(mean_l), 1),
                    })
                    sweep_id += 1

    return pd.DataFrame(rows)


def generate_robustness(samples_df):
    robust_samples = samples_df.sample(5, random_state=SEED + 1)["sample_id"].tolist()
    downsampling_factors = [1, 2, 3, 4]
    noise_levels = [0.0, 0.05, 0.10, 0.15, 0.20]
    rows = []
    robustness_id = 1

    for sid in robust_samples:
        base_row = samples_df[samples_df["sample_id"] == sid].iloc[0]
        for ds in downsampling_factors:
            for noise in noise_levels:
                degradation = (ds - 1) * 0.12 + noise * 1.5
                noise_val = rng.normal(0, 0.03)
                fiber_count = int(base_row["fiber_count"] * max(0.2, 1 - degradation * 0.3 + noise_val))
                contact_count = int(base_row["contact_count"] * max(0.1, 1 - degradation * 0.4 + noise_val))
                mean_d = base_row["mean_diameter_um"] * (1 + degradation * 0.05 + rng.normal(0, 0.01))
                orient_disp = base_row["orientation_dispersion"] * (1 + degradation * 0.1 + rng.normal(0, 0.02))
                quality = max(1, min(5, int(5 - degradation * 1.5 + rng.normal(0, 0.5))))
                rows.append({
                    "robustness_id": f"R{robustness_id:05d}",
                    "sample_id": sid,
                    "downsampling_factor": ds,
                    "noise_level": noise,
                    "fiber_count": max(5, fiber_count),
                    "contact_count": max(0, contact_count),
                    "mean_diameter_um": round(float(mean_d), 2),
                    "orientation_dispersion": round(float(orient_disp), 2),
                    "quality_score": quality,
                })
                robustness_id += 1

    return pd.DataFrame(rows)


def generate_acoustic_thermal(samples_df):
    rows = []
    completed = samples_df[samples_df["status"] == "completed"]

    for _, row in completed.iterrows():
        porosity = row["porosity"]
        mean_d = row["mean_diameter_um"]
        orient_disp = row["orientation_dispersion"]

        airflow_res = 1000 * (1 - porosity) ** 1.8 / (mean_d ** 1.5) * rng.uniform(0.85, 1.15) * 1e4
        thermal_perm = (mean_d ** 2 * porosity ** 2.2) / (180 * (1 - porosity) ** 2) * rng.uniform(0.9, 1.1) * 1e-12
        viscous_length = mean_d * porosity / (2 * (1 - porosity)) * rng.uniform(0.8, 1.2)
        thermal_length = 2 * viscous_length * rng.uniform(1.0, 1.5)

        absorptions = {}
        for freq, label in [(250, "250hz"), (500, "500hz"), (1000, "1000hz"), (2000, "2000hz"), (4000, "4000hz")]:
            base = 0.3 + 0.5 * porosity - 0.01 * np.log10(airflow_res / 1e4 + 1e-9)
            freq_boost = 0.1 * np.log10(freq / 250 + 1)
            absorptions[f"absorption_{label}"] = round(float(min(0.99, max(0.01, base + freq_boost + rng.normal(0, 0.03)))), 3)

        def noisy(val, scale=0.15):
            return round(float(val * (1 + rng.normal(0, scale))), 6)

        rows.append({
            "sample_id": row["sample_id"],
            "porosity": porosity,
            "mean_diameter_um": mean_d,
            "orientation_dispersion": orient_disp,
            "airflow_resistivity": round(float(airflow_res), 1),
            "thermal_permeability": round(float(thermal_perm), 4),
            "viscous_length_um": round(float(viscous_length), 2),
            "thermal_length_um": round(float(thermal_length), 2),
            "predicted_airflow_resistivity": noisy(airflow_res),
            "predicted_thermal_permeability": noisy(thermal_perm),
            "predicted_viscous_length_um": noisy(viscous_length),
            "predicted_thermal_length_um": noisy(thermal_length),
            **absorptions,
        })

    return pd.DataFrame(rows)


def generate_quality_log(samples_df):
    rows = []
    log_id = 1
    issue_descriptions = {
        "artifact": ["Bright ring artifact near volume boundary", "Beam hardening artifact detected",
                     "Motion artifact from scanner vibration"],
        "low_contrast": ["Low contrast between fiber and matrix", "Scan underexposed",
                         "Fiber boundary poorly defined"],
        "incomplete_volume": ["Volume cropped at edge", "Partial fiber bundle at Z boundary",
                              "Missing slices in stack"],
        "segmentation_error": ["Threshold too high, fibers merged", "Background misclassified as fiber",
                                "Watershed over-segmentation"],
        "oversized_object": ["Large cluster not separated", "Bundle of parallel fibers merged",
                             "Binder blob included in fiber segment"],
        "noise": ["Salt-and-pepper noise in background", "Gaussian noise above 5%",
                  "Scan noise affects small fiber detection"],
        "ok": ["No issues detected", "Passed all quality checks", "Clean scan"],
    }

    for _, sample in samples_df.iterrows():
        n_issues = rng.integers(1, 5)
        issue_types_sampled = rng.choice(ISSUE_TYPES, size=n_issues,
                                          p=[0.10, 0.10, 0.08, 0.12, 0.08, 0.10, 0.42])
        for issue in issue_types_sampled:
            severity = "low" if issue == "ok" else rng.choice(SEVERITIES, p=[0.5, 0.35, 0.15])
            rows.append({
                "log_id": f"L{log_id:05d}",
                "sample_id": sample["sample_id"],
                "issue_type": issue,
                "severity": severity,
                "description": random.choice(issue_descriptions[issue]),
                "detected_by": rng.choice(["auto", "manual"], p=[0.7, 0.3]),
                "resolved": bool(rng.choice([True, False], p=[0.65, 0.35])),
            })
            log_id += 1

    return pd.DataFrame(rows)


def main():
    print("Generating samples.csv...")
    samples = generate_samples()
    samples.to_csv(os.path.join(DATA_DIR, "samples.csv"), index=False)
    print(f"  → {len(samples)} samples")

    print("Generating fibers.csv...")
    fibers = generate_fibers(samples)
    fibers.to_csv(os.path.join(DATA_DIR, "fibers.csv"), index=False)
    print(f"  → {len(fibers)} fibers")

    print("Generating contacts.csv...")
    contacts = generate_contacts(fibers)
    contacts.to_csv(os.path.join(DATA_DIR, "contacts.csv"), index=False)
    print(f"  → {len(contacts)} contacts")

    print("Generating parameter_sweep.csv...")
    sweep = generate_parameter_sweep(samples)
    sweep.to_csv(os.path.join(DATA_DIR, "parameter_sweep.csv"), index=False)
    print(f"  → {len(sweep)} sweep entries")

    print("Generating robustness.csv...")
    robustness = generate_robustness(samples)
    robustness.to_csv(os.path.join(DATA_DIR, "robustness.csv"), index=False)
    print(f"  → {len(robustness)} robustness entries")

    print("Generating acoustic_thermal.csv...")
    acoustic = generate_acoustic_thermal(samples)
    acoustic.to_csv(os.path.join(DATA_DIR, "acoustic_thermal.csv"), index=False)
    print(f"  → {len(acoustic)} acoustic/thermal entries")

    print("Generating quality_log.csv...")
    quality = generate_quality_log(samples)
    quality.to_csv(os.path.join(DATA_DIR, "quality_log.csv"), index=False)
    print(f"  → {len(quality)} quality log entries")

    print("\nAll mock data generated successfully.")


if __name__ == "__main__":
    main()
