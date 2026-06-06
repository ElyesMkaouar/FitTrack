import pytest
import pandas as pd

from utils.metrics import taux_progression, progression_exercice, records_personnels
from pipeline.transform import ajoute_volume, ajoute_1rm_epley


# ── taux_progression ──────────────────────────────────────────────────────────

def test_taux_progression_positif():
    assert taux_progression(100, 120) == pytest.approx(20.0)

def test_taux_progression_negatif():
    assert taux_progression(100, 80) == pytest.approx(-20.0)

def test_taux_progression_identique():
    assert taux_progression(100, 100) == pytest.approx(0.0)

def test_taux_progression_debut_zero():
    assert taux_progression(0, 100) == 0.0


# ── ajoute_volume / ajoute_1rm_epley ─────────────────────────────────────────

def test_ajoute_volume():
    df = pd.DataFrame([{"repetitions": 10, "charge_kg": 100.0}])
    assert ajoute_volume(df)["volume"].iloc[0] == pytest.approx(1000.0)

def test_ajoute_1rm_epley():
    # Epley : 100 * (1 + 10/30) = 133.33
    df = pd.DataFrame([{"charge_kg": 100.0, "repetitions": 10}])
    assert ajoute_1rm_epley(df)["one_rm"].iloc[0] == pytest.approx(133.33, rel=1e-3)


# ── progression_exercice ──────────────────────────────────────────────────────

def _df_progression():
    return pd.DataFrame([
        {"exercice_id": 1, "date": pd.Timestamp(f"2025-{m:02d}-15"), "charge_kg": 100 + m * 5}
        for m in range(1, 7)
    ])

def test_progression_exercice_croissante():
    assert progression_exercice(_df_progression()) > 0

def test_progression_exercice_exercice_inconnu():
    assert progression_exercice(pd.DataFrame(columns=["exercice_id", "date", "charge_kg"])) == 0.0

def test_progression_exercice_un_seul_mois():
    df = pd.DataFrame([{"exercice_id": 1, "date": pd.Timestamp("2025-01-15"), "charge_kg": 100}])
    assert progression_exercice(df) == 0.0


# ── records_personnels ────────────────────────────────────────────────────────

def test_records_personnels():
    df = pd.DataFrame([
        {"exercice_id": 1, "date": pd.Timestamp("2025-01-01"), "charge_kg": 100.0, "volume": 600.0},
        {"exercice_id": 1, "date": pd.Timestamp("2025-01-01"), "charge_kg": 105.0, "volume": 630.0},
        {"exercice_id": 1, "date": pd.Timestamp("2025-01-08"), "charge_kg": 102.0, "volume": 612.0},
    ])
    r = records_personnels(df)
    assert r["charge_max"] == pytest.approx(105.0)
    assert r["volume_max_seance"] == pytest.approx(1230.0)

def test_records_personnels_vide():
    df = pd.DataFrame(columns=["exercice_id", "charge_kg", "volume", "date"])
    r = records_personnels(df)
    assert r["charge_max"] == 0.0
    assert r["volume_max_seance"] == 0.0
