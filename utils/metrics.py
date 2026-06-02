import pandas as pd


# ── Formules atomiques ────────────────────────────────────────────────────────

def taux_progression(valeur_debut: float, valeur_fin: float) -> float:
    """Taux de progression en % entre deux valeurs."""
    if valeur_debut == 0:
        return 0.0
    return (valeur_fin - valeur_debut) / valeur_debut * 100


# ── KPIs globaux ──────────────────────────────────────────────────────────────

def kpi_global(df: pd.DataFrame) -> dict:
    """Retourne les 4 KPIs de la page Vue globale."""
    nb_seances = df["date"].nunique()
    volume_total = df["volume"].sum()

    exercice_plus_pratique = df.groupby("nom")["date"].nunique().idxmax() # exo le plus présent dans les séances pas forcément le plus pratiqué

    meilleur_1rm_row = df.loc[df["one_rm"].idxmax()]
    meilleur_1rm = {
        "exercice": meilleur_1rm_row["nom"],
        "valeur": round(meilleur_1rm_row["one_rm"], 1),
    }

    return {
        "nb_seances": nb_seances,
        "volume_total": round(volume_total, 1),
        "exercice_plus_pratique": exercice_plus_pratique,
        "meilleur_1rm": meilleur_1rm,
    }


# ── Métriques par exercice ────────────────────────────────────────────────────

def progression_exercice(df: pd.DataFrame, exercice_id: int) -> float:
    """
    Taux de progression (%) entre le premier et le dernier mois
    pour un exercice donné — basé sur la charge maximale mensuelle.
    """
    filtre = df[df["exercice_id"] == exercice_id].copy()
    if filtre.empty:
        return 0.0

    filtre["periode"] = filtre["date"].dt.to_period("M")
    charge_par_mois = filtre.groupby("periode")["charge_kg"].max().sort_index()

    if len(charge_par_mois) < 2:
        return 0.0

    n = min(2, len(charge_par_mois) // 2)
    debut = charge_par_mois.iloc[:n].mean()
    fin = charge_par_mois.iloc[-n:].mean()
    return taux_progression(debut, fin)


def records_personnels(df: pd.DataFrame, exercice_id: int) -> dict:
    """Charge max et volume max sur une séance pour un exercice."""
    filtre = df[df["exercice_id"] == exercice_id]
    if filtre.empty:
        return {"charge_max": 0.0, "volume_max_seance": 0.0}

    charge_max = filtre["charge_kg"].max()

    volume_par_seance = filtre.groupby("date")["volume"].sum()
    volume_max = volume_par_seance.max()

    return {
        "charge_max": round(charge_max, 1),
        "volume_max_seance": round(volume_max, 1),
    }


# ── Fréquence d'entraînement (heatmap) ───────────────────────────────────────

def frequence_par_jour(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retourne un DataFrame pivot (semaines * jours) du nombre
    d'exercices distincts pratiqués chaque jour — pour la heatmap.
    """
    freq = df.groupby("date", as_index=False)["exercice_id"].nunique().rename(columns={"exercice_id": "nb_exercices"})
    freq["semaine_iso"] = freq["date"].dt.isocalendar().week.astype(int)
    freq["annee_iso"] = freq["date"].dt.isocalendar().year.astype(int)
    freq["jour_num"] = freq["date"].dt.dayofweek
    return freq
