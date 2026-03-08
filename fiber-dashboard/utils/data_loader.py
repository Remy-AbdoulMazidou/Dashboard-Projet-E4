import os
import subprocess
import sys
import pandas as pd
import functools

from config import DATA_FILES, BASE_DIR


def _ensure_data_exists():
    missing = [k for k, path in DATA_FILES.items() if not os.path.exists(path)]
    if missing:
        script = os.path.join(BASE_DIR, "scripts", "generate_mock_data.py")
        subprocess.run([sys.executable, script], check=True)


@functools.lru_cache(maxsize=None)
def load_samples() -> pd.DataFrame:
    _ensure_data_exists()
    df = pd.read_csv(DATA_FILES["samples"], parse_dates=["processing_date"])
    return df


@functools.lru_cache(maxsize=None)
def load_fibers() -> pd.DataFrame:
    _ensure_data_exists()
    return pd.read_csv(DATA_FILES["fibers"])


@functools.lru_cache(maxsize=None)
def load_contacts() -> pd.DataFrame:
    _ensure_data_exists()
    return pd.read_csv(DATA_FILES["contacts"])


@functools.lru_cache(maxsize=None)
def load_parameter_sweep() -> pd.DataFrame:
    _ensure_data_exists()
    return pd.read_csv(DATA_FILES["parameter_sweep"])


@functools.lru_cache(maxsize=None)
def load_robustness() -> pd.DataFrame:
    _ensure_data_exists()
    return pd.read_csv(DATA_FILES["robustness"])


@functools.lru_cache(maxsize=None)
def load_acoustic_thermal() -> pd.DataFrame:
    _ensure_data_exists()
    return pd.read_csv(DATA_FILES["acoustic_thermal"])


@functools.lru_cache(maxsize=None)
def load_quality_log() -> pd.DataFrame:
    _ensure_data_exists()
    return pd.read_csv(DATA_FILES["quality_log"])


def filter_samples(materials=None, batches=None, statuses=None) -> pd.DataFrame:
    df = load_samples()
    if materials:
        df = df[df["material"].isin(materials)]
    if batches:
        df = df[df["batch"].isin(batches)]
    if statuses:
        df = df[df["status"].isin(statuses)]
    return df
