import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "workouts.xlsx"


# ── Chargement ────────────────────────────────────────────────────────────────

def load_raw(path: Path = DATA_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    xl = pd.ExcelFile(path, engine="openpyxl")
    seances = xl.parse("seances", parse_dates=["date"])
    exercices = xl.parse("exercices")
    calendrier = xl.parse("calendrier", parse_dates=["date"])
    return seances, exercices, calendrier


# ── Étapes de transformation ──────────────────────────────────────────────────

def normalise_unites(df: pd.DataFrame) -> pd.DataFrame:
    """Convertit les lignes en lbs → kg (1 lbs = 0.453592 kg)."""
    mask = df["unite"].str.lower() == "lbs"
    df = df.copy()
    df.loc[mask, "charge_kg"] = df.loc[mask, "charge_kg"] * 0.453592
    df.loc[mask, "unite"] = "kg"
    return df


def ajoute_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Volume par série = répétitions × charge_kg."""
    df = df.copy()
    df["volume"] = df["repetitions"] * df["charge_kg"]
    return df


def ajoute_1rm_epley(df: pd.DataFrame) -> pd.DataFrame:
    """1RM estimé (Epley) : charge × (1 + reps / 30)."""
    df = df.copy()
    df["one_rm"] = df["charge_kg"] * (1 + df["repetitions"] / 30)
    return df


def merge_dimensions(
    seances: pd.DataFrame,
    exercices: pd.DataFrame,
    calendrier: pd.DataFrame,
) -> pd.DataFrame:
    """Jointure fait + dimensions → table analytique plate."""
    df = (
        seances
        .merge(exercices, on="exercice_id", how="left")
        .merge(calendrier, on="date", how="left")
    )
    return df


# ── Pipeline principal ────────────────────────────────────────────────────────

def build_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    """
    Pipeline complet :
      1. Chargement Excel
      2. Merge dimensions
      3. Normalisation unités
      4. Calcul volume
      5. Calcul 1RM Epley
    """
    seances, exercices, calendrier = load_raw(path)

    df = (
        merge_dimensions(seances, exercices, calendrier)
        .pipe(normalise_unites)
        .pipe(ajoute_volume)
        .pipe(ajoute_1rm_epley)
    )
    return df


# ── Agrégations temporelles ───────────────────────────────────────────────────

def volume_par_semaine(df: pd.DataFrame) -> pd.DataFrame:
    """Volume total par semaine ISO (année + numéro de semaine)."""
    tmp = df.copy()
    tmp["annee_iso"] = tmp["date"].dt.isocalendar().year.astype(int)
    return tmp.groupby(["annee_iso", "semaine"], as_index=False)["volume"].sum().assign(label=lambda x: x["annee_iso"].astype(str) + "-S" + x["semaine"].astype(str).str.zfill(2)).sort_values(["annee_iso", "semaine"])


def volume_par_mois(df: pd.DataFrame) -> pd.DataFrame:
    """Volume total par mois."""
    return df.groupby(["annee", "mois"], as_index=False)["volume"].sum().sort_values(["annee", "mois"])


def charge_max_par_exercice_date(df: pd.DataFrame) -> pd.DataFrame:
    """Charge maximale atteinte par exercice et par date."""
    return (
        df.groupby(["date", "exercice_id", "nom"], as_index=False)["charge_kg"].max().sort_values(["exercice_id", "date"])
    )


def one_rm_max_par_exercice_date(df: pd.DataFrame) -> pd.DataFrame:
    """1RM estimé maximal par exercice et par date."""
    return df.groupby(["date", "exercice_id", "nom"], as_index=False)["one_rm"].max().sort_values(["exercice_id", "date"])
