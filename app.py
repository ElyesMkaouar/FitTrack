import streamlit as st
from pipeline.transform import build_dataset
import views.vue_globale as vue_globale
import views.par_exercice as par_exercice
import views.historique as historique

# Abréviations de mois en français (indépendant de la locale système)
MOIS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
           "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def _mois_annee_fr(ts) -> str:
    """Formate un Timestamp en 'mois année' français (ex. 'nov. 2025')."""
    return f"{MOIS_FR[ts.month - 1]} {ts.year}"

st.set_page_config(
    page_title="FitTrack",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data():
    return build_dataset()


def main() -> None:
    st.sidebar.title("FitTrack")
    st.sidebar.caption("Dashboard analytique d'entraînement")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        ["Vue globale", "Par exercice", "Historique"],
        label_visibility="collapsed",
    )

    df = load_data()

    if page == "Vue globale":
        vue_globale.render(df)
    elif page == "Par exercice":
        par_exercice.render(df)
    else:
        historique.render(df)

    st.sidebar.divider()
    st.sidebar.caption(
        f"Données : {_mois_annee_fr(df['date'].min())} – {_mois_annee_fr(df['date'].max())}  \n"
        f"{df['date'].nunique()} jours d'entraînement"
    )


if __name__ == "__main__":
    main()
