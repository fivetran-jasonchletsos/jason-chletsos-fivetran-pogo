"""
Pokémon GO Analytics — Streamlit App
Reads directly from Snowflake POKEMON_MARTS schema.
"""

import os
import textwrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from snowflake.connector import connect
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    Encoding,
    PrivateFormat,
    NoEncryption,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pokémon GO Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Snowflake connection ────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to Snowflake…")
def get_connection():
    """
    Supports two auth modes:
      1. Local dev  — reads the encrypted PEM key from disk (SNOWFLAKE_PRIVATE_KEY_PATH +
                      SNOWFLAKE_PRIVATE_KEY_PASSPHRASE env vars, or the defaults below)
      2. AWS deploy — pass the raw PEM content as SNOWFLAKE_PRIVATE_KEY_CONTENT env var
                      (stored in AWS Secrets Manager and injected at runtime)
    """
    account    = os.environ.get("SNOWFLAKE_ACCOUNT",   "A3209653506471-SALES_ENG_DEMO")
    user       = os.environ.get("SNOWFLAKE_USER",      "JASON.CHLETSOS@FIVETRAN.COM")
    role       = os.environ.get("SNOWFLAKE_ROLE",      "SALES_DEMO_ROLE")
    warehouse  = os.environ.get("SNOWFLAKE_WAREHOUSE", "DEFAULT")
    database   = os.environ.get("SNOWFLAKE_DATABASE",  "jason_chletsos")

    pem_content = os.environ.get("SNOWFLAKE_PRIVATE_KEY_CONTENT")

    if pem_content:
        # AWS path — key content injected as env var
        pem_bytes = pem_content.encode()
        passphrase = None
    else:
        # Local dev path — read from disk
        key_path   = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "/Users/jason.chletsos/rsa_key.p8")
        passphrase_str = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "Guy2001@#!")
        with open(key_path, "rb") as f:
            pem_bytes = f.read()
        passphrase = passphrase_str.encode() if passphrase_str else None

    private_key = load_pem_private_key(pem_bytes, password=passphrase)
    private_key_der = private_key.private_bytes(
        encoding=Encoding.DER,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )

    return connect(
        account=account,
        user=user,
        role=role,
        warehouse=warehouse,
        database=database,
        private_key=private_key_der,
    )


@st.cache_data(ttl=3600, show_spinner="Querying Snowflake…")
def query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql(textwrap.dedent(sql), conn)


# ── Sidebar navigation ─────────────────────────────────────────────────────────
PAGES = [
    "🏠 Overview",
    "⚔️  Top Attackers",
    "🛡️  Top Defenders",
    "🌟 Legendaries",
    "💥 Best Movesets",
    "🔥 Type Effectiveness",
    "📊 Stats by Type",
]

st.sidebar.image(
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png",
    width=60,
)
st.sidebar.title("Pokémon GO Analytics")
st.sidebar.caption("Powered by PokéAPI · Fivetran · Snowflake · dbt")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption("Data refreshes every hour. Source: `JASON_CHLETSOS.POKEMON_MARTS`")


# ── Helper ─────────────────────────────────────────────────────────────────────
TYPE_COLORS = {
    "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0",
    "electric": "#F8D030", "grass": "#78C850", "ice": "#98D8D8",
    "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
    "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8",
    "dark": "#705848", "steel": "#B8B8D0", "fairy": "#EE99AC",
}

def type_color(type_name):
    return TYPE_COLORS.get(str(type_name).lower(), "#888888")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Overview
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.title("⚡ Pokémon GO Analytics")
    st.caption("An end-to-end pipeline: PokéAPI → Fivetran → Snowflake → dbt → Streamlit")

    # Scorecards
    df_counts = query("""
        SELECT
            COUNT(*)                                                AS total_pokemon,
            SUM(CASE WHEN is_legendary OR is_mythical THEN 1 END)  AS legendary_mythical,
            SUM(CASE WHEN secondary_type IS NOT NULL  THEN 1 END)  AS dual_type
        FROM POKEMON_MARTS.DIM_POKEMON
    """)
    df_moves = query("SELECT COUNT(*) AS total_moves FROM POKEMON_MARTS.DIM_MOVES")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pokémon",        f"{int(df_counts['TOTAL_POKEMON'][0]):,}")
    c2.metric("Total Moves",          f"{int(df_moves['TOTAL_MOVES'][0]):,}")
    c3.metric("Legendary / Mythical", f"{int(df_counts['LEGENDARY_MYTHICAL'][0]):,}")
    c4.metric("Dual-type",            f"{int(df_counts['DUAL_TYPE'][0]):,}")

    st.divider()

    col_left, col_right = st.columns(2)

    # Pokémon by primary type
    with col_left:
        st.subheader("Pokémon by Primary Type")
        df_types = query("""
            SELECT primary_type, COUNT(*) AS pokemon_count
            FROM POKEMON_MARTS.DIM_POKEMON
            WHERE primary_type IS NOT NULL
            GROUP BY primary_type
            ORDER BY pokemon_count DESC
        """)
        df_types.columns = df_types.columns.str.lower()
        fig = px.bar(
            df_types, x="pokemon_count", y="primary_type",
            orientation="h",
            color="primary_type",
            color_discrete_map=TYPE_COLORS,
            labels={"pokemon_count": "# Pokémon", "primary_type": ""},
        )
        fig.update_layout(showlegend=False, height=500, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    # Tier breakdown (attackers)
    with col_right:
        st.subheader("Attacker Tier Distribution")
        df_tier = query("""
            SELECT tier, COUNT(*) AS pokemon_count
            FROM POKEMON_MARTS.MART_TOP_ATTACKERS
            GROUP BY tier
            ORDER BY tier
        """)
        df_tier.columns = df_tier.columns.str.lower()
        fig2 = px.pie(
            df_tier, names="tier", values="pokemon_count",
            color="tier",
            color_discrete_map={"S": "#FFD700", "A": "#C0C0C0", "B": "#CD7F32", "C": "#888"},
            hole=0.4,
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        fig2.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Top Attackers
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚔️  Top Attackers":
    st.title("⚔️ Top Attackers")

    top_n = st.slider("Show top N Pokémon", 10, 100, 25)
    legendary_filter = st.checkbox("Include Legendaries & Mythicals", value=True)

    where = "" if legendary_filter else "WHERE is_legendary = FALSE AND is_mythical = FALSE"

    df = query(f"""
        SELECT pokemon_name, primary_type, secondary_type,
               attack, sp_attack, total_base_stats, tier,
               is_legendary, is_mythical, overall_rank
        FROM POKEMON_MARTS.MART_TOP_ATTACKERS
        {where}
        ORDER BY overall_rank
        LIMIT {top_n}
    """)
    df.columns = df.columns.str.lower()

    # Bar chart
    fig = px.bar(
        df, x="attack", y="pokemon_name",
        orientation="h",
        color="primary_type",
        color_discrete_map=TYPE_COLORS,
        hover_data=["sp_attack", "total_base_stats", "tier"],
        labels={"attack": "Attack Stat", "pokemon_name": ""},
    )
    fig.update_layout(
        height=max(400, top_n * 22),
        yaxis={"categoryorder": "total ascending"},
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Attack vs Sp. Attack scatter
    st.subheader("Attack vs Special Attack")
    fig2 = px.scatter(
        df, x="attack", y="sp_attack",
        color="primary_type",
        color_discrete_map=TYPE_COLORS,
        size="total_base_stats",
        hover_name="pokemon_name",
        text="tier",
        labels={"attack": "Attack", "sp_attack": "Sp. Attack"},
    )
    fig2.update_traces(textposition="top center")
    fig2.update_layout(height=450)
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Top Defenders
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🛡️  Top Defenders":
    st.title("🛡️ Top Defenders")

    top_n = st.slider("Show top N Pokémon", 10, 100, 25)
    legendary_filter = st.checkbox("Include Legendaries & Mythicals", value=True)

    where = "" if legendary_filter else "WHERE is_legendary = FALSE AND is_mythical = FALSE"

    df = query(f"""
        SELECT pokemon_name, primary_type, secondary_type,
               hp, defense, sp_defense, combined_defensive_stat,
               total_base_stats, tier, is_legendary, is_mythical, overall_rank
        FROM POKEMON_MARTS.MART_TOP_DEFENDERS
        {where}
        ORDER BY overall_rank
        LIMIT {top_n}
    """)
    df.columns = df.columns.str.lower()

    fig = px.bar(
        df, x="combined_defensive_stat", y="pokemon_name",
        orientation="h",
        color="primary_type",
        color_discrete_map=TYPE_COLORS,
        hover_data=["hp", "defense", "sp_defense", "tier"],
        labels={"combined_defensive_stat": "Defense + HP", "pokemon_name": ""},
    )
    fig.update_layout(
        height=max(400, top_n * 22),
        yaxis={"categoryorder": "total ascending"},
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Stacked bar: HP vs Defense vs Sp. Defense
    st.subheader("Defensive Stat Breakdown")
    df_melt = df[["pokemon_name", "hp", "defense", "sp_defense"]].melt(
        id_vars="pokemon_name", var_name="stat", value_name="value"
    ).head(top_n * 3)
    fig2 = px.bar(
        df_melt, x="value", y="pokemon_name",
        orientation="h", color="stat", barmode="stack",
        labels={"value": "Stat Value", "pokemon_name": ""},
        color_discrete_map={"hp": "#E74C3C", "defense": "#3498DB", "sp_defense": "#9B59B6"},
    )
    fig2.update_layout(height=max(400, top_n * 22), yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Legendaries
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌟 Legendaries":
    st.title("🌟 Legendary & Mythical Rankings")

    df = query("""
        SELECT overall_rank, pokemon_name, primary_type, secondary_type,
               rarity_tier, generation, total_base_stats,
               hp, attack, defense, sp_attack, sp_defense, speed
        FROM POKEMON_MARTS.MART_LEGENDARY_RANKINGS
        ORDER BY overall_rank
    """)
    df.columns = df.columns.str.lower()

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            df.head(40), x="total_base_stats", y="pokemon_name",
            orientation="h",
            color="rarity_tier",
            color_discrete_map={"Legendary": "#FFD700", "Mythical": "#FF69B4"},
            hover_data=["primary_type", "generation"],
            labels={"total_base_stats": "Total Base Stats", "pokemon_name": ""},
        )
        fig.update_layout(height=900, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("By Generation")
        df_gen = df.groupby("generation").size().reset_index(name="count")
        fig2 = px.pie(df_gen, names="generation", values="count", hole=0.35)
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Legendary vs Mythical")
        df_rarity = df.groupby("rarity_tier").size().reset_index(name="count")
        fig3 = px.pie(
            df_rarity, names="rarity_tier", values="count",
            color="rarity_tier",
            color_discrete_map={"Legendary": "#FFD700", "Mythical": "#FF69B4"},
            hole=0.35,
        )
        fig3.update_layout(height=350)
        st.plotly_chart(fig3, use_container_width=True)

    # Stat radar for selected Pokémon
    st.divider()
    st.subheader("Stat Comparison")
    selected = st.multiselect(
        "Pick up to 5 Pokémon to compare",
        options=df["pokemon_name"].tolist(),
        default=df["pokemon_name"].head(3).tolist(),
        max_selections=5,
    )
    if selected:
        stats = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]
        fig_radar = go.Figure()
        for name in selected:
            row = df[df["pokemon_name"] == name].iloc[0]
            vals = [row[s] for s in stats] + [row[stats[0]]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=stats + [stats[0]],
                fill="toself", name=name,
            ))
        fig_radar.update_layout(
            polar={"radialaxis": {"visible": True, "range": [0, 260]}},
            height=450,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Best Movesets
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💥 Best Movesets":
    st.title("💥 Best Movesets")

    col1, col2, col3 = st.columns(3)
    stab_only   = col1.checkbox("STAB moves only", value=False)
    dmg_class   = col2.selectbox("Damage class", ["All", "physical", "special"])
    top_n       = col3.slider("Top N moves", 20, 200, 50)

    where_clauses = []
    if stab_only:
        where_clauses.append("is_stab = TRUE")
    if dmg_class != "All":
        where_clauses.append(f"damage_class = '{dmg_class}'")
    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    df = query(f"""
        SELECT pokemon_name, primary_type, move_name, move_type,
               damage_class, power, accuracy, expected_damage, is_stab, move_rank
        FROM POKEMON_MARTS.MART_BEST_MOVESETS
        {where}
        ORDER BY expected_damage DESC NULLS LAST
        LIMIT {top_n}
    """)
    df.columns = df.columns.str.lower()

    fig = px.bar(
        df, x="expected_damage", y="pokemon_name",
        orientation="h",
        color="move_type",
        color_discrete_map=TYPE_COLORS,
        hover_data=["move_name", "power", "accuracy", "damage_class", "is_stab"],
        labels={"expected_damage": "Expected Damage (power × accuracy)", "pokemon_name": ""},
    )
    fig.update_layout(
        height=max(400, top_n * 18),
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Move power distribution
    st.subheader("Move Power Distribution")
    df_dist = query("""
        SELECT damage_class,
            CASE
                WHEN power < 40  THEN '1: <40'
                WHEN power < 60  THEN '2: 40-59'
                WHEN power < 80  THEN '3: 60-79'
                WHEN power < 100 THEN '4: 80-99'
                WHEN power < 120 THEN '5: 100-119'
                ELSE                  '6: 120+'
            END AS power_bucket,
            COUNT(*) AS move_count
        FROM POKEMON_MARTS.DIM_MOVES
        WHERE power IS NOT NULL
          AND damage_class IN ('physical', 'special')
        GROUP BY damage_class, power_bucket
        ORDER BY damage_class, power_bucket
    """)
    df_dist.columns = df_dist.columns.str.lower()
    fig2 = px.bar(
        df_dist, x="power_bucket", y="move_count",
        color="damage_class", barmode="group",
        color_discrete_map={"physical": "#E74C3C", "special": "#3498DB"},
        labels={"power_bucket": "Power Range", "move_count": "# Moves"},
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Type Effectiveness
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔥 Type Effectiveness":
    st.title("🔥 Type Effectiveness Matrix")
    st.caption("How much damage does each **attacking type** deal to each **defending type**?")

    df = query("""
        SELECT attacking_type, defending_type, effectiveness_multiplier
        FROM POKEMON_MARTS.MART_TYPE_EFFECTIVENESS
        ORDER BY attacking_type, defending_type
    """)
    df.columns = df.columns.str.lower()

    pivot = df.pivot(index="attacking_type", columns="defending_type", values="effectiveness_multiplier")

    fig = px.imshow(
        pivot,
        color_continuous_scale=[
            [0.0,  "#000000"],   # 0x  — immune
            [0.25, "#C0392B"],   # 0.5x — not very effective
            [0.5,  "#ECF0F1"],   # 1x  — neutral
            [0.75, "#27AE60"],   # 2x  — super effective
            [1.0,  "#1A5276"],   # 4x  — double super effective (rare)
        ],
        zmin=0, zmax=4,
        aspect="auto",
        labels={"x": "Defending Type", "y": "Attacking Type", "color": "Multiplier"},
        text_auto=True,
    )
    fig.update_layout(
        height=650,
        coloraxis_colorbar={"title": "Multiplier", "tickvals": [0, 0.5, 1, 2, 4]},
        xaxis={"tickangle": -45},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Filter to a single attacking type
    st.divider()
    st.subheader("Drill into a single type")
    all_types = sorted(df["attacking_type"].unique().tolist())
    chosen = st.selectbox("Select attacking type", all_types, index=all_types.index("fire") if "fire" in all_types else 0)
    df_single = df[df["attacking_type"] == chosen].sort_values("effectiveness_multiplier", ascending=False)
    fig2 = px.bar(
        df_single, x="defending_type", y="effectiveness_multiplier",
        color="defending_type",
        color_discrete_map=TYPE_COLORS,
        labels={"effectiveness_multiplier": "Multiplier", "defending_type": "Defending Type"},
    )
    fig2.add_hline(y=1, line_dash="dash", line_color="gray", annotation_text="Neutral (1×)")
    fig2.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Stats by Type
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Stats by Type":
    st.title("📊 Average Base Stats by Type")

    df = query("""
        SELECT d.primary_type, f.stat_name,
               ROUND(AVG(f.base_stat_value), 1) AS avg_base_stat
        FROM POKEMON_MARTS.FCT_POKEMON_STATS f
        JOIN POKEMON_MARTS.DIM_POKEMON d ON f.pokemon_id = d.pokemon_id
        WHERE d.primary_type IS NOT NULL
          AND f.stat_name IN ('attack','defense','hp','speed','special-attack','special-defense')
        GROUP BY d.primary_type, f.stat_name
        ORDER BY d.primary_type, f.stat_name
    """)
    df.columns = df.columns.str.lower()

    stat_choice = st.multiselect(
        "Stats to display",
        options=["attack", "defense", "hp", "speed", "special-attack", "special-defense"],
        default=["attack", "defense", "hp"],
    )
    df_filtered = df[df["stat_name"].isin(stat_choice)]

    fig = px.bar(
        df_filtered, x="primary_type", y="avg_base_stat",
        color="stat_name", barmode="group",
        labels={"avg_base_stat": "Avg Base Stat", "primary_type": "Primary Type", "stat_name": "Stat"},
    )
    fig.update_layout(height=450, xaxis={"tickangle": -45})
    st.plotly_chart(fig, use_container_width=True)

    # Attack vs Defense scatter across all Pokémon
    st.subheader("Attack vs Defense — All Pokémon")
    df_scatter = query("""
        SELECT d.pokemon_name, d.primary_type,
               f.attack, f.defense, f.hp, f.total_base_stats,
               d.is_legendary, d.is_mythical
        FROM POKEMON_MARTS.FCT_POKEMON_STATS f
        JOIN POKEMON_MARTS.DIM_POKEMON d ON f.pokemon_id = d.pokemon_id
        WHERE f.attack IS NOT NULL AND f.defense IS NOT NULL
    """)
    df_scatter.columns = df_scatter.columns.str.lower()

    show_legendary = st.checkbox("Highlight Legendaries", value=True)
    if show_legendary:
        df_scatter["category"] = df_scatter.apply(
            lambda r: "Mythical" if r["is_mythical"] else ("Legendary" if r["is_legendary"] else r["primary_type"]),
            axis=1,
        )
        color_col = "category"
    else:
        color_col = "primary_type"

    fig2 = px.scatter(
        df_scatter, x="attack", y="defense",
        color=color_col,
        color_discrete_map=TYPE_COLORS,
        size="total_base_stats",
        hover_name="pokemon_name",
        hover_data=["hp", "total_base_stats"],
        opacity=0.7,
        labels={"attack": "Attack", "defense": "Defense"},
    )
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, use_container_width=True)
