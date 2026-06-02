import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.metrics import kpi_global
from pipeline.transform import volume_par_semaine


def render(df: pd.DataFrame) -> None:
    st.header("Vue globale")

    _render_kpis(df)
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        _render_volume_hebdo(df)
    with col2:
        _render_repartition_groupes(df)


def _render_kpis(df: pd.DataFrame) -> None:
    kpis = kpi_global(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Séances totales", kpis["nb_seances"])
    c2.metric("Volume total (kg)", f"{kpis['volume_total']:,.0f}".replace(",", " "))
    c3.metric("Exercice le + pratiqué", kpis["exercice_plus_pratique"])
    c4.metric(
        f"Meilleur 1RM — {kpis['meilleur_1rm']['exercice']}",
        f"{kpis['meilleur_1rm']['valeur']} kg",
    )


def _render_volume_hebdo(df: pd.DataFrame) -> None:
    st.subheader("Volume hebdomadaire (kg)")
    hebdo = volume_par_semaine(df)

    fig = px.area(
        hebdo,
        x="label",
        y="volume",
        labels={"label": "Semaine", "volume": "Volume (kg)"},
        color_discrete_sequence=["#6366f1"],
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        xaxis_tickangle=-45,
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_traces(
        hovertemplate="Volume : %{y:.0f} kg<extra></extra>",
        line_width=2,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_repartition_groupes(df: pd.DataFrame) -> None:
    st.subheader("Groupes musculaires")

    repartition = df.groupby("groupe_musculaire", as_index=False)["volume"].sum().sort_values("volume", ascending=False)

    fig = px.pie(
        repartition,
        names="groupe_musculaire",
        values="volume",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>%{value:.0f} kg<br>%{percent}",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
