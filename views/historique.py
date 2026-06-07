import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.metrics import frequence_par_jour


def render(df: pd.DataFrame) -> None:
    st.header("Historique & Calendrier")

    col1, col2, col3 = st.columns(3)

    with col1:
        date_min = df["date"].min().date()
        date_max = df["date"].max().date()
        plage = st.date_input(
            "Période",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
        )

    with col2:
        groupes = ["Tous"] + sorted(df["groupe_musculaire"].unique().tolist())
        groupe_choix = st.selectbox("Groupe musculaire", groupes)

    with col3:
        exercices = ["Tous"] + sorted(df["nom"].unique().tolist())
        ex_choix = st.selectbox("Exercice", exercices)

    filtre = _appliquer_filtres(df, plage, groupe_choix, ex_choix)

    st.divider()
    _render_tableau(filtre)
    st.divider()
    _render_heatmap(filtre)


def _appliquer_filtres(df: pd.DataFrame, plage, groupe: str, exercice: str) -> pd.DataFrame:
    filtre = df.copy()

    if isinstance(plage, (list, tuple)) and len(plage) == 2:
        debut, fin = pd.Timestamp(plage[0]), pd.Timestamp(plage[1])
        filtre = filtre[(filtre["date"] >= debut) & (filtre["date"] <= fin)]

    if groupe != "Tous":
        filtre = filtre[filtre["groupe_musculaire"] == groupe]

    if exercice != "Tous":
        filtre = filtre[filtre["nom"] == exercice]

    return filtre


def _render_tableau(filtre: pd.DataFrame) -> None:
    st.subheader(f"Séances ({len(filtre)} séries)")

    affichage = (
        filtre[["date", "nom", "groupe_musculaire", "serie", "repetitions", "charge_kg", "volume", "one_rm", "notes"]]
        .copy()
        .sort_values(["date", "nom", "serie"], ascending=[False, True, True])
        .rename(columns={
            "date": "Date",
            "nom": "Exercice",
            "groupe_musculaire": "Groupe",
            "serie": "N° Série",
            "repetitions": "Reps",
            "charge_kg": "Charge (kg)",
            "volume": "Volume (kg)",
            "one_rm": "1RM estimé",
            "notes": "Notes",
        })
    )
    affichage["Charge (kg)"] = affichage["Charge (kg)"].round(1)
    affichage["Volume (kg)"] = affichage["Volume (kg)"].round(1)
    affichage["1RM estimé"] = affichage["1RM estimé"].round(1)
    affichage["Notes"] = affichage["Notes"].fillna("")
    affichage["Date"] = affichage["Date"].dt.strftime("%Y-%m-%d")

    st.dataframe(affichage, use_container_width=True, hide_index=True, height=400)


def _render_heatmap(df: pd.DataFrame) -> None:
    st.subheader("Fréquence d'entraînement")

    freq = frequence_par_jour(df)

    semaines = sorted(freq["semaine_programme"].unique().tolist())
    semaine_idx = {s: i for i, s in enumerate(semaines)}

    z = np.zeros((7, len(semaines)))
    for _, row in freq.iterrows():
        col = semaine_idx.get(row["semaine_programme"])
        if col is not None:
            z[int(row["jour_num"]), col] = row["nb_exercices"]

    jours_labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    x_labels = [f"S{str(s).zfill(2)}" for s in semaines]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=x_labels,
        y=jours_labels,
        zmin=0,
        colorscale=[
            [0.0,   "#1e1e2e"],  # repos : gris sombre, discret
            [0.001, "#ede9fe"],  # activité minimale : très clair (vues filtrées)
            [0.55,  "#c084fc"],  # palier intermédiaire
            [0.8,   "#a855f7"],  # 4 exercices : violet vif (clair)
            [1.0,   "#3b0764"],  # 5 exercices : violet très sombre (max)
        ],
        showscale=True,
        hovertemplate="Semaine %{x}<br>%{y}<br>%{z} exercices<extra></extra>",
        xgap=2,
        ygap=2,
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=40, r=0, t=8, b=40),
        xaxis=dict(tickangle=-45, showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=False),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="#fafafa",
    )
    st.plotly_chart(fig, use_container_width=True)
