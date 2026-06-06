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

def progression_exercice(df: pd.DataFrame) -> float:
    """
    Taux de progression (%) entre le premier et le dernier mois
    pour un exercice donné — basé sur la charge maximale mensuelle.
    """
    if df.empty:
        return 0.0

    df = df.copy()
    df["periode"] = df["date"].dt.to_period("M")
    charge_par_mois = df.groupby("periode")["charge_kg"].max().sort_index()

    if len(charge_par_mois) < 2:
        return 0.0

    # Dataset fixé à 6 mois : on compare les 3 premiers vs les 3 derniers
    debut = charge_par_mois.iloc[:3].mean()
    fin = charge_par_mois.iloc[-3:].mean()
    return taux_progression(debut, fin)


def records_personnels(df: pd.DataFrame) -> dict:
    """Charge max et volume max sur une séance pour un exercice."""
    if df.empty:
        return {"charge_max": 0.0, "volume_max_seance": 0.0}

    charge_max = df["charge_kg"].max()

    volume_par_seance = df.groupby("date")["volume"].sum()
    volume_max = volume_par_seance.max()

    return {
        "charge_max": round(charge_max, 1),
        "volume_max_seance": round(volume_max, 1),
    }


# ── Répartition par groupe musculaire ────────────────────────────────────────

def repartition_groupes(df: pd.DataFrame) -> pd.DataFrame:
    """Volume total par groupe musculaire, trié décroissant."""
    return df.groupby("groupe_musculaire", as_index=False)["volume"].sum().sort_values("volume", ascending=False)


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
