import pandas as pd
import streamlit as st
import os
import plotly.express as px
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Équipe", layout="wide")

@st.cache_data
def load_data(path):
    return pd.read_csv(path, encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.basename(BASE_DIR) == "pages":
    BASE_DIR = os.path.dirname(BASE_DIR)

CSV_PATH = os.path.join(BASE_DIR, "data", "archive", "club_stats", "2024_season_club_stats.csv")

CSV_PATH_STAT_PLAYER_OK = os.path.join(BASE_DIR, "data", "archive", "stats_player_ok.csv")


df2 = load_data(CSV_PATH)
st.session_state["df2"] = df2

df3 = load_data(CSV_PATH_STAT_PLAYER_OK)
st.session_state["df3"] = df3

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

# Représentation des nationalités

# ---- Contrôles UI ----
with st.expander("Options d'affichage", expanded=False):
    donut = st.checkbox("Afficher en donut", value=False)
    group_small = st.checkbox("Regrouper les petites nationalités dans « Autres »", value=True)
    mode_group = st.radio("Méthode de regroupement", ["Top N", "Seuil %"], index=0, horizontal=True, disabled=not group_small)
    colA, colB = st.columns(2)
    with colA:
        top_n = st.slider("Top N à conserver", 3, 15, 8, disabled=not group_small or mode_group != "Top N")
    with colB:
        min_pct = st.slider("Seuil % minimum", 1, 20, 5, disabled=not group_small or mode_group != "Seuil %")

# Normaliser les noms d'équipe pour matcher proprement
team_norm = str(team).strip().lower()
df3_norm = df3.assign(
    player_club=df3["player_club"].astype(str).str.strip(),
    Nationality=df3["Nationality"].astype(str).str.strip(),
)

# Filtre sur l'équipe (insensible à la casse)
mask_team = df3_norm["player_club"].str.lower().eq(team_norm)
team_players = df3_norm.loc[mask_team & df3_norm["Nationality"].ne("")].copy()

if team_players.empty:
    st.warning("Aucun joueur trouvé pour cette équipe dans le fichier des stats joueurs.")
else:
    # Comptage par nationalité
    counts = (
        team_players["Nationality"]
        .value_counts(dropna=True)
        .rename_axis("Nationality")
        .reset_index(name="Players")
    )

    # Regroupement "Autres"
    if group_small:
        if mode_group == "Top N":
            if len(counts) > top_n:
                top = counts.head(top_n)
                autres_sum = counts["Players"].iloc[top_n:].sum()
                counts = pd.concat(
                    [top, pd.DataFrame([{"Nationality": "Autres", "Players": autres_sum}])],
                    ignore_index=True
                )
        else:  # Seuil %
            total_tmp = counts["Players"].sum()
            # Garde ceux >= seuil, regroupe le reste
            keep = counts[(counts["Players"] / total_tmp * 100) >= min_pct]
            others = counts[(counts["Players"] / total_tmp * 100) < min_pct]
            if not others.empty:
                autres_sum = others["Players"].sum()
                counts = pd.concat(
                    [keep, pd.DataFrame([{"Nationality": "Autres", "Players": autres_sum}])],
                    ignore_index=True
                ).sort_values("Players", ascending=False)

    total_players = counts["Players"].sum()
    counts["%"] = (counts["Players"] / total_players * 100).round(1)

    # Tableau récap
    st.dataframe(
        counts,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Nationality": st.column_config.TextColumn("Nationalité"),
            "Players": st.column_config.NumberColumn("Joueurs"),
            "%": st.column_config.NumberColumn("Pourcentage", format="%.1f %%"),
        },
    )

    # Camembert / Donut
    fig = px.pie(
        counts,
        names="Nationality",
        values="Players",
        title=f"Nationalités — {team} ({int(total_players)} joueurs)",
        hole=0.4 if donut else 0.0,
    )
    fig.update_traces(textposition="inside", textinfo="label+percent")
    st.plotly_chart(fig, use_container_width=True)

# --- Effectif par poste (avec recherche) ---
st.subheader("👥 Voir effectif")

# Normalisation de base
df3_norm_pos = df3.assign(
    player_club=df3["player_club"].astype(str).str.strip(),
    player_position=df3["player_position"].astype(str).str.strip(),
)

# Filtre équipe
mask_team_pos = df3_norm_pos["player_club"].str.lower().eq(team_norm)
squad = df3_norm_pos.loc[mask_team_pos].copy()

squad["Age"] = pd.to_datetime(squad["Date of Birth"], format="%d/%m/%Y", errors="coerce").dt.year
squad["Age"] = datetime.now().year - squad["Age"]

squad["Match_Joués"] = np.where(squad["Appearances"] != 0, squad["Appearances"], squad["appearances_"])

if squad.empty:
    st.warning("Aucun joueur trouvé pour cette équipe dans le fichier des stats joueurs.")
else:
    # --- Champ de recherche ---
    with st.expander("🔎 Rechercher un joueur", expanded=False):
        query_player = st.text_input("Nom du joueur", placeholder="Tape une partie du nom...")

    # Colonnes à afficher si présentes

    display_cols = ["player_name", "Nationality", "Age", "Match_Joués", "Goals", "Assists"]

    # --- Application du filtre de recherche ---
    if query_player:
        q = query_player.strip().lower()
        mask_name = squad["player_name"].astype(str).str.lower().str.contains(q, na=False)
        squad = squad.loc[mask_name].copy()
        if squad.empty:
            st.info("Aucun joueur ne correspond à la recherche.")
        
    # Comptes par poste (badges)
    counts_by_group = squad["player_position"].value_counts().to_dict()
    order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
    groups = [g for g in order if g in counts_by_group] or sorted(counts_by_group.keys())

    tabs = st.tabs([f"{g} ({counts_by_group.get(g, 0)})" for g in groups])

    for tab, g in zip(tabs, groups):
        with tab:
            block = (
                squad.loc[squad["player_position"].eq(g), display_cols]
                .rename(columns={"player_name": "Joueur"})
                .sort_values("Match_Joués", ascending=False)
                .reset_index(drop=True)
            )

            st.dataframe(
                block,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Joueur": st.column_config.TextColumn("Joueur"),
                    "Nationality": st.column_config.TextColumn("Nationalité"),
                    "Age": st.column_config.NumberColumn("Âge"),
                    "Match_Joués": st.column_config.NumberColumn("Matchs joués"),
                    "Goals": st.column_config.NumberColumn("Buts"),
                    "Assists": st.column_config.NumberColumn("Passes D")
                },
            )


# Lien retour
st.page_link("Dashboard.py", label="⬅️ Retour à la Home Page")



