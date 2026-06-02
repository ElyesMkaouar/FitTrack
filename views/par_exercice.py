import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.metrics import records_personnels, progression_exercice
from pipeline.transform import charge_max_par_exercice_date, one_rm_max_par_exercice_date


def render(df: pd.DataFrame) -> None:
    st.header("Par exercice")

    exercices = df[["exercice_id", "nom"]].drop_duplicates().sort_values("nom")
    noms = exercices["nom"].tolist()

    choix = st.selectbox("Exercice", noms)
    ex_id = int(exercices.loc[exercices["nom"] == choix, "exercice_id"].iloc[0])

    filtre = df[df["exercice_id"] == ex_id].copy()

    st.divider()
    _render_records(filtre, ex_id, choix)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        _render_charge_max(filtre)
    with col2:
        _render_1rm(filtre)

    st.divider()
    _render_progression(filtre)


def _render_records(filtre: pd.DataFrame, exercice_id: int, nom: str) -> None:
    pr = records_personnels(filtre, exercice_id)
    prog = progression_exercice(filtre, exercice_id)

    st.subheader(f"Records — {nom}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Charge max", f"{pr['charge_max']} kg")
    c2.metric("Volume max (séance)", f"{pr['volume_max_seance']:,.0f} kg".replace(",", " "))
    c3.metric("Progression 6 mois", f"{prog:+.1f}%")


def _render_charge_max(filtre: pd.DataFrame) -> None:
    st.subheader("Charge maximale")

    charge_par_date = charge_max_par_exercice_date(filtre).sort_values("date")

    fig = px.line(
        charge_par_date,
        x="date",
        y="charge_kg",
        labels={"date": "Date", "charge_kg": "Charge (kg)"},
        markers=True,
        color_discrete_sequence=["#6366f1"],
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_traces(hovertemplate="%{y:.1f} kg")
    st.plotly_chart(fig, use_container_width=True)


def _render_1rm(filtre: pd.DataFrame) -> None:
    st.subheader("1RM estimé (Epley)")

    one_rm_par_date = one_rm_max_par_exercice_date(filtre).sort_values("date")

    fig = px.line(
        one_rm_par_date,
        x="date",
        y="one_rm",
        labels={"date": "Date", "one_rm": "1RM estimé (kg)"},
        markers=True,
        color_discrete_sequence=["#f59e0b"],
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_traces(hovertemplate="%{y:.1f} kg")
    st.plotly_chart(fig, use_container_width=True)


def _render_progression(filtre: pd.DataFrame) -> None:
    st.subheader("Charge maximale par mois")

    filtre = filtre.copy()
    filtre["periode"] = filtre["date"].dt.to_period("M")

    mensuel = filtre.groupby("periode", as_index=False)["charge_kg"].max().sort_values("periode")
    mensuel["periode_str"] = mensuel["periode"].astype(str)
    mensuel["delta_pct"] = mensuel["charge_kg"].pct_change() * 100

    fig = go.Figure()
    fig.add_bar(
        x=mensuel["periode_str"],
        y=mensuel["charge_kg"],
        marker_color="#6366f1",
        name="Charge max",
        hovertemplate="%{x}<br>%{y:.1f} kg",
    )
    fig.update_layout(
        xaxis_title="Mois",
        yaxis_title="Charge max (kg)",
        margin=dict(l=0, r=0, t=8, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    mensuel_display = mensuel[["periode_str", "charge_kg", "delta_pct"]].copy()
    mensuel_display.columns = ["Mois", "Charge max (kg)", "Δ vs mois préc. (%)"]
    mensuel_display["Charge max (kg)"] = mensuel_display["Charge max (kg)"].round(1)
    mensuel_display["Δ vs mois préc. (%)"] = mensuel_display["Δ vs mois préc. (%)"].apply(
        lambda x: f"{x:+.1f}%" if pd.notna(x) else "—"
    )
    st.dataframe(mensuel_display, use_container_width=True, hide_index=True)
