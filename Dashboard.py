import streamlit as st 
import pandas as pd

st.set_page_config(page_title="Home Page", layout="wide")
st.title("Home Page")

@st.cache_data
def load_data(path):
    return pd.read_csv(path, encoding="utf-8")

CSV_PATH = "C:/Users/pierr/Documents/Analyse_Stat_Pl/data/archive/Classement_2024.csv"

df = load_data(CSV_PATH)
st.session_state["df"] = df

# --- Liste d'équipes propres ---
equipes = sorted(df["name"].dropna().astype(str).str.strip())
equipes_lower_map = {e.lower(): e for e in equipes}  # pour retrouver la casse exacte

# --- Barre de recherche avec submit ---
with st.form("search_team_form", clear_on_submit=False):
    query = st.text_input("🔍 Rechercher une équipe", placeholder="Tape le nom de l'équipe...")
    submitted = st.form_submit_button("Rechercher")

if submitted and query:
    q = query.strip().lower()

    # 1) Match EXACT insensible à la casse
    if q in equipes_lower_map:
        st.session_state["selected_team"] = equipes_lower_map[q]
        st.switch_page("pages/Equipe.py")

    # 2) Sinon, si une SEULE correspondance partielle -> on prend
    partial = [e for e in equipes if q in e.lower()]
    if len(partial) == 1:
        st.session_state["selected_team"] = partial[0]
        st.switch_page("pages/Equipe.py")
    elif len(partial) == 0:
        st.warning("Aucune équipe ne correspond à la recherche.")
    else:
        st.info("Plusieurs équipes correspondent, précise ta recherche ou clique sur un bouton ci-dessous.")

# --- Sélection des équipes (boutons) ---
st.subheader("Équipes")
n_cols = 4
cols = st.columns(n_cols)

# Si une recherche est en cours, on filtre l'affichage des boutons
current_query = (query or "").strip().lower()
equipes_affichees = [e for e in equipes if current_query in e.lower()] if current_query else equipes

for i, team in enumerate(equipes_affichees):
    if cols[i % n_cols].button(team, use_container_width=True, key=f"btn_{team}"):
        st.session_state["selected_team"] = team
        st.switch_page("pages/Equipe.py")

# --- Classement croissant par position ---
st.subheader("Classement 24/25")

classement = (
    df.assign(
        name=df["name"].astype(str).str.strip(),
        position=pd.to_numeric(df["position"], errors="coerce")
    )
    .dropna(subset=["name", "position", "badge_url"])  # On garde que ceux avec logo
    .drop_duplicates(subset=["name"])
    .sort_values("position", ascending=True)
    .loc[:, ["badge_url", "name", "points", "games_played", "games_won", "games_lost", "games_drawn", "goals_for", "goals_against", "goal_difference"]]
    .reset_index(drop=True)
    .rename(columns={
        "badge_url": "Logo",
        "name": "Équipe",
        "points": "PTS",
        "games_played": "J",
        "games_won": "G",
        "games_lost": "P",
        "games_drawn": "N",
        "goals_for": "GF",
        "goals_against": "GA",
        "goal_difference": "+/-"
    })
)

st.dataframe(
    classement,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Logo": st.column_config.ImageColumn("Logo", width="small")
    }
)


