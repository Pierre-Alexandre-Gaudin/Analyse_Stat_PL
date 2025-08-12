import pandas as pd
import streamlit as st

st.set_page_config(page_title="Équipe", layout="wide")

@st.cache_data
def load_data(path):
    return pd.read_csv(path, encoding="utf-8")

CSV_PATH = "C:/Users/pierr/Documents/Analyse_Stat_Pl/data/archive/club_stats/2024_season_club_stats.csv"

df2 = load_data(CSV_PATH)
st.session_state["df2"] = df2

team = st.session_state.get("selected_team")
df = st.session_state.get("df")

st.title(f"Statistique 24/25 {team if team else ''}")

# Vérif données
if not team or not isinstance(df, pd.DataFrame):
    st.warning("Aucune équipe ou données introuvables. Retourne à l’accueil.")
    st.page_link("Dashboard.py", label="⬅️ Retour à la Home Page")
    st.stop()

# Normaliser et filtrer
mask = df["name"].astype(str).str.strip().eq(str(team).strip())
match = df.loc[mask]

if match.empty:
    st.warning("Équipe introuvable dans les données.")
    st.page_link("Dashboard.py", label="⬅️ Retour à la Home Page")
    st.stop()

# Classement
classement = match["position"].iloc[0]

# Associer un trophée selon le classement
trophees = {
    1: "🏆🥇",  # trophée + médaille or
    2: "🥈",    # médaille argent
    3: "🥉"     # médaille bronze
}

# Affichage nom + trophée si dans top 3
if classement in trophees:
    st.subheader(f"{team} {trophees[classement]}")
else:
    st.subheader(team)

# Tableau filtré
subset = (
    match[["position", "points", "games_won", "games_drawn", "games_lost", "goals_for", "goals_against"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

# Affichage tableau avec index masqué
st.dataframe(
    subset,
    hide_index=True,
    column_config={
        "position": st.column_config.NumberColumn("Classement"),
        "points": st.column_config.NumberColumn("Points"),
        "games_won": st.column_config.NumberColumn("Match gagné"),
        "games_drawn": st.column_config.NumberColumn("Match nul"),
        "games_lost": st.column_config.NumberColumn("Match perdu"),
        "goals_for": st.column_config.NumberColumn("Nombre de but marqué"),
        "goals_against": st.column_config.NumberColumn("Nombre de but encaissé"),
    },
    use_container_width=True,
)





# Lien retour
st.page_link("Dashboard.py", label="⬅️ Retour à la Home Page")



