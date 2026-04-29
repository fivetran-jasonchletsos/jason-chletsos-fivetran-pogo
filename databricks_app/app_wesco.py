"""
Pokémon GO Analytics — Wesco Edition
Branded for Wesco International presentation.
Reads from Databricks Unity Catalog: jason_chletsos.pokemon_marts
"""

import base64
import os
import textwrap
import traceback

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from databricks import sql as dbsql

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pokémon GO Analytics | Wesco",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Wesco brand colours ────────────────────────────────────────────────────────
WESCO_GREEN      = "#00AA13"
WESCO_GREEN_DARK = "#007D0E"
WESCO_GREEN_LITE = "#33BB3F"
WESCO_NAVY       = "#0D1B2A"
WESCO_DARK       = "#111827"
WESCO_CARD       = "#1A2535"
WESCO_BORDER     = "#1F3044"
WESCO_TEXT       = "#F0F4F8"
WESCO_MUTED      = "#8A9BB0"

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* ── Base ── */
  html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
      background-color: {WESCO_NAVY} !important;
      color: {WESCO_TEXT} !important;
      font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
  }}
  [data-testid="stSidebar"] {{
      background-color: {WESCO_DARK} !important;
      border-right: 1px solid {WESCO_BORDER};
  }}
  [data-testid="stSidebar"] * {{
      color: {WESCO_TEXT} !important;
  }}

  /* ── Sidebar nav radio ── */
  [data-testid="stSidebar"] [role="radiogroup"] label {{
      border-radius: 6px;
      padding: 6px 10px;
      margin-bottom: 2px;
      transition: background 0.15s;
  }}
  [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
      background: {WESCO_BORDER} !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {{
      background: {WESCO_GREEN} !important;
  }}

  /* ── Metric cards ── */
  [data-testid="stMetric"] {{
      background: {WESCO_CARD};
      border: 1px solid {WESCO_BORDER};
      border-top: 3px solid {WESCO_GREEN};
      border-radius: 8px;
      padding: 16px 20px !important;
  }}
  [data-testid="stMetricLabel"] {{ color: {WESCO_MUTED} !important; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }}
  [data-testid="stMetricValue"] {{ color: {WESCO_TEXT} !important; font-size: 2rem !important; font-weight: 700; }}

  /* ── Headings ── */
  h1, h2, h3, h4 {{ color: {WESCO_TEXT} !important; }}
  h1 {{ border-bottom: 2px solid {WESCO_GREEN}; padding-bottom: 8px; }}

  /* ── Divider ── */
  hr {{ border-color: {WESCO_BORDER} !important; }}

  /* ── Expander ── */
  [data-testid="stExpander"] {{
      background: {WESCO_CARD};
      border: 1px solid {WESCO_BORDER};
      border-radius: 8px;
  }}

  /* ── Dataframe ── */
  [data-testid="stDataFrame"] {{ border: 1px solid {WESCO_BORDER}; border-radius: 8px; }}

  /* ── Selectbox / Slider labels ── */
  label, .stSelectbox label, .stSlider label, .stCheckbox label {{
      color: {WESCO_MUTED} !important;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
  }}

  /* ── Caption ── */
  [data-testid="stCaptionContainer"] {{ color: {WESCO_MUTED} !important; }}

  /* ── Powered-by banner ── */
  .wesco-banner {{
      background: linear-gradient(90deg, {WESCO_GREEN_DARK} 0%, {WESCO_GREEN} 100%);
      border-radius: 8px;
      padding: 10px 18px;
      font-size: 0.82rem;
      color: #fff;
      margin-bottom: 12px;
      letter-spacing: 0.03em;
  }}

  /* ── Section header pill ── */
  .section-pill {{
      display: inline-block;
      background: {WESCO_GREEN};
      color: #fff;
      border-radius: 4px;
      padding: 2px 10px;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 6px;
  }}
</style>
""", unsafe_allow_html=True)

# ── Wesco logo (inline SVG from file) ─────────────────────────────────────────
_LOGO_PATH = os.path.join(os.path.dirname(__file__), "wesco_logo.svg")
_LOGO_PATH_ALT = "/wesco_logo.svg"  # fallback absolute path

def _load_logo() -> str:
    for p in [_LOGO_PATH, _LOGO_PATH_ALT]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/svg+xml;base64,{b64}" style="width:160px; margin-bottom:8px;">'
    return "<b style='color:#00AA13;font-size:1.4rem;'>WESCO</b>"

# ── Sidebar ────────────────────────────────────────────────────────────────────
PAGES = [
    "🏠 Overview",
    "⚔️  Top Attackers",
    "🛡️  Top Defenders",
    "🌟 Legendaries",
    "💥 Best Movesets",
    "🔥 Type Effectiveness",
    "📊 Stats by Type",
]

st.sidebar.markdown(_load_logo(), unsafe_allow_html=True)
st.sidebar.markdown(
    f"<div style='color:{WESCO_MUTED};font-size:0.72rem;text-transform:uppercase;"
    f"letter-spacing:0.08em;margin-bottom:12px;'>Pokémon GO Analytics</div>",
    unsafe_allow_html=True,
)
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown(
    f"<div style='color:{WESCO_MUTED};font-size:0.72rem;'>"
    f"Data refreshes every hour.<br>"
    f"Source: <code>jason_chletsos.pokemon_marts</code><br><br>"
    f"<span style='color:{WESCO_GREEN};'>●</span> Powered by Fivetran · Databricks · dbt"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Type colour map ────────────────────────────────────────────────────────────
TYPE_COLORS = {
    "normal": "#A8A878",   "fire": "#F08030",    "water": "#6890F0",
    "electric": "#F8D030", "grass": "#78C850",   "ice": "#98D8D8",
    "fighting": "#C03028", "poison": "#A040A0",  "ground": "#E0C068",
    "flying": "#A890F0",   "psychic": "#F85888", "bug": "#A8B820",
    "rock": "#B8A038",     "ghost": "#705898",   "dragon": "#7038F8",
    "dark": "#705848",     "steel": "#B8B8D0",   "fairy": "#EE99AC",
}

CATALOG = "jason_chletsos"
SCHEMA  = "pokemon_marts"

# ── Plotly theme defaults ──────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#131F2E",
    font_color=WESCO_TEXT,
    font_family="Segoe UI, Inter, Arial, sans-serif",
    xaxis=dict(gridcolor=WESCO_BORDER, zerolinecolor=WESCO_BORDER),
    yaxis=dict(gridcolor=WESCO_BORDER, zerolinecolor=WESCO_BORDER),
    colorway=[WESCO_GREEN, "#3498DB", "#E74C3C", "#F39C12", "#9B59B6",
              "#1ABC9C", "#E67E22", "#2ECC71", "#E91E63", "#00BCD4"],
)

def apply_wesco_theme(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig

# ── Databricks connection ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_connection():
    host      = os.environ.get("DATABRICKS_HOST",      "dbc-c48d38b1-67f3.cloud.databricks.com")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH")
    token     = os.environ.get("DATABRICKS_TOKEN")

    if not http_path or not token:
        raise ValueError(
            "DATABRICKS_HTTP_PATH and DATABRICKS_TOKEN environment variables are required."
        )

    conn = dbsql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
        catalog=CATALOG,
        schema=SCHEMA,
    )
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
    return conn


def get_conn_safe():
    try:
        return get_connection(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"


@st.cache_data(ttl=3600, show_spinner="Loading data…")
def query(sql: str) -> pd.DataFrame:
    conn, err = get_conn_safe()
    if err:
        st.error(f"Databricks connection failed:\n```\n{err}\n```")
        st.stop()
    try:
        with conn.cursor() as cur:
            cur.execute(textwrap.dedent(sql))
            rows = cur.fetchall()
            cols = [d[0].lower() for d in cur.description]
            return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        st.error(f"Query failed: {type(e).__name__}: {e}")
        st.code(traceback.format_exc())
        st.stop()


# ── Connection check ───────────────────────────────────────────────────────────
conn, conn_err = get_conn_safe()
if conn_err:
    st.error("Could not connect to Databricks. Details below:")
    st.code(conn_err)
    st.stop()


# ── Powered-by banner (top of every page) ─────────────────────────────────────
st.markdown(
    "<div class='wesco-banner'>"
    "⚡&nbsp; <strong>Live Data Pipeline</strong> &nbsp;·&nbsp; "
    "PokéAPI &nbsp;→&nbsp; Fivetran &nbsp;→&nbsp; Databricks &nbsp;→&nbsp; dbt &nbsp;→&nbsp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Overview
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.title("Pokémon GO Analytics")
    st.caption("Real-time Pokémon data powering smarter decisions — built on Fivetran & Databricks")

    with st.spinner("Loading overview…"):
        df_counts = query(f"""
            SELECT
                COUNT(*)                                                      AS total_pokemon,
                SUM(CASE WHEN is_legendary OR is_mythical THEN 1 ELSE 0 END) AS legendary_mythical,
                SUM(CASE WHEN secondary_type IS NOT NULL  THEN 1 ELSE 0 END) AS dual_type
            FROM {CATALOG}.{SCHEMA}.dim_pokemon
        """)
        df_moves = query(f"SELECT COUNT(*) AS total_moves FROM {CATALOG}.{SCHEMA}.dim_moves")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pokémon",        f"{int(df_counts['total_pokemon'][0]):,}")
    c2.metric("Total Moves",          f"{int(df_moves['total_moves'][0]):,}")
    c3.metric("Legendary / Mythical", f"{int(df_counts['legendary_mythical'][0]):,}")
    c4.metric("Dual-type",            f"{int(df_counts['dual_type'][0]):,}")

    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("<div class='section-pill'>Distribution</div>", unsafe_allow_html=True)
        st.subheader("Pokémon by Primary Type")
        df_types = query(f"""
            SELECT primary_type, COUNT(*) AS pokemon_count
            FROM {CATALOG}.{SCHEMA}.dim_pokemon
            WHERE primary_type IS NOT NULL
            GROUP BY primary_type
            ORDER BY pokemon_count DESC
        """)
        fig = px.bar(
            df_types, x="pokemon_count", y="primary_type", orientation="h",
            color="primary_type", color_discrete_map=TYPE_COLORS,
            labels={"pokemon_count": "# Pokémon", "primary_type": ""},
        )
        fig.update_layout(showlegend=False, height=500, yaxis={"categoryorder": "total ascending"})
        apply_wesco_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("<div class='section-pill'>Tiers</div>", unsafe_allow_html=True)
        st.subheader("Attacker Tier Distribution")
        df_tier = query(f"""
            SELECT tier, COUNT(*) AS pokemon_count
            FROM {CATALOG}.{SCHEMA}.mart_top_attackers
            GROUP BY tier ORDER BY tier
        """)
        fig2 = px.pie(
            df_tier, names="tier", values="pokemon_count",
            color="tier",
            color_discrete_map={"S": WESCO_GREEN, "A": "#3498DB", "B": "#E67E22", "C": WESCO_MUTED},
            hole=0.45,
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label",
                           marker=dict(line=dict(color=WESCO_NAVY, width=2)))
        fig2.update_layout(showlegend=False, height=500)
        apply_wesco_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Top Attackers
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚔️  Top Attackers":
    st.title("Top Attackers")

    col_a, col_b, col_c = st.columns(3)
    top_n = col_a.slider("Show top N Pokémon", 10, 100, 25)
    legendary_filter = col_b.checkbox("Include Legendaries & Mythicals", value=True)
    where = "" if legendary_filter else "WHERE is_legendary = FALSE AND is_mythical = FALSE"

    with st.spinner("Loading attackers…"):
        df = query(f"""
            SELECT pokemon_name, primary_type, secondary_type,
                   attack, sp_attack, total_base_stats, tier,
                   is_legendary, is_mythical, overall_rank
            FROM {CATALOG}.{SCHEMA}.mart_top_attackers
            {where}
            ORDER BY overall_rank
            LIMIT {top_n}
        """)

    st.markdown("<div class='section-pill'>Attack Ranking</div>", unsafe_allow_html=True)
    fig = px.bar(
        df, x="attack", y="pokemon_name", orientation="h",
        color="primary_type", color_discrete_map=TYPE_COLORS,
        hover_data=["sp_attack", "total_base_stats", "tier"],
        labels={"attack": "Attack Stat", "pokemon_name": ""},
    )
    fig.update_layout(height=max(400, top_n * 22), yaxis={"categoryorder": "total ascending"})
    apply_wesco_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-pill'>Attack vs Sp. Attack</div>", unsafe_allow_html=True)
    st.subheader("Attack vs Special Attack")
    fig2 = px.scatter(
        df, x="attack", y="sp_attack",
        color="primary_type", color_discrete_map=TYPE_COLORS,
        size="total_base_stats", hover_name="pokemon_name", text="tier",
        labels={"attack": "Attack", "sp_attack": "Sp. Attack"},
    )
    fig2.update_traces(textposition="top center")
    fig2.update_layout(height=450)
    apply_wesco_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════���═══════════════════════════════════════════
# PAGE: Top Defenders
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🛡️  Top Defenders":
    st.title("Top Defenders")

    col_a, col_b = st.columns(2)
    top_n = col_a.slider("Show top N Pokémon", 10, 100, 25)
    legendary_filter = col_b.checkbox("Include Legendaries & Mythicals", value=True)
    where = "" if legendary_filter else "WHERE is_legendary = FALSE AND is_mythical = FALSE"

    with st.spinner("Loading defenders…"):
        df = query(f"""
            SELECT pokemon_name, primary_type, secondary_type,
                   hp, defense, sp_defense, combined_defensive_stat,
                   total_base_stats, tier, is_legendary, is_mythical, overall_rank
            FROM {CATALOG}.{SCHEMA}.mart_top_defenders
            {where}
            ORDER BY overall_rank
            LIMIT {top_n}
        """)

    st.markdown("<div class='section-pill'>Defense Ranking</div>", unsafe_allow_html=True)
    fig = px.bar(
        df, x="combined_defensive_stat", y="pokemon_name", orientation="h",
        color="primary_type", color_discrete_map=TYPE_COLORS,
        hover_data=["hp", "defense", "sp_defense", "tier"],
        labels={"combined_defensive_stat": "Defense + HP", "pokemon_name": ""},
    )
    fig.update_layout(height=max(400, top_n * 22), yaxis={"categoryorder": "total ascending"})
    apply_wesco_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-pill'>Stat Breakdown</div>", unsafe_allow_html=True)
    st.subheader("Defensive Stat Breakdown")
    df_melt = df[["pokemon_name", "hp", "defense", "sp_defense"]].melt(
        id_vars="pokemon_name", var_name="stat", value_name="value"
    )
    fig2 = px.bar(
        df_melt, x="value", y="pokemon_name", orientation="h",
        color="stat", barmode="stack",
        labels={"value": "Stat Value", "pokemon_name": ""},
        color_discrete_map={"hp": "#E74C3C", "defense": WESCO_GREEN, "sp_defense": "#3498DB"},
    )
    fig2.update_layout(height=max(400, top_n * 22), yaxis={"categoryorder": "total ascending"})
    apply_wesco_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Legendaries
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌟 Legendaries":
    st.title("Legendary & Mythical Rankings")

    with st.spinner("Loading legendaries…"):
        df = query(f"""
            SELECT overall_rank, pokemon_name, primary_type, secondary_type,
                   rarity_tier, generation, total_base_stats,
                   hp, attack, defense, sp_attack, sp_defense, speed
            FROM {CATALOG}.{SCHEMA}.mart_legendary_rankings
            ORDER BY overall_rank
        """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<div class='section-pill'>Rankings</div>", unsafe_allow_html=True)
        fig = px.bar(
            df.head(40), x="total_base_stats", y="pokemon_name", orientation="h",
            color="rarity_tier",
            color_discrete_map={"Legendary": WESCO_GREEN, "Mythical": "#3498DB"},
            hover_data=["primary_type", "generation"],
            labels={"total_base_stats": "Total Base Stats", "pokemon_name": ""},
        )
        fig.update_layout(height=900, yaxis={"categoryorder": "total ascending"})
        apply_wesco_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='section-pill'>By Generation</div>", unsafe_allow_html=True)
        df_gen = df.groupby("generation").size().reset_index(name="count")
        fig2 = px.pie(df_gen, names="generation", values="count", hole=0.4)
        fig2.update_traces(marker=dict(line=dict(color=WESCO_NAVY, width=2)))
        fig2.update_layout(height=350)
        apply_wesco_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<div class='section-pill'>Rarity Split</div>", unsafe_allow_html=True)
        df_rarity = df.groupby("rarity_tier").size().reset_index(name="count")
        fig3 = px.pie(
            df_rarity, names="rarity_tier", values="count",
            color="rarity_tier",
            color_discrete_map={"Legendary": WESCO_GREEN, "Mythical": "#3498DB"},
            hole=0.4,
        )
        fig3.update_traces(marker=dict(line=dict(color=WESCO_NAVY, width=2)))
        fig3.update_layout(height=350)
        apply_wesco_theme(fig3)
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    st.markdown("<div class='section-pill'>Stat Radar</div>", unsafe_allow_html=True)
    st.subheader("Stat Comparison Radar")
    selected = st.multiselect(
        "Pick up to 5 Pokémon to compare",
        options=df["pokemon_name"].tolist(),
        default=df["pokemon_name"].head(3).tolist(),
        max_selections=5,
    )
    if selected:
        stats = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]
        fig_radar = go.Figure()
        palette = [WESCO_GREEN, "#3498DB", "#E74C3C", "#F39C12", "#9B59B6"]
        for i, name in enumerate(selected):
            row = df[df["pokemon_name"] == name].iloc[0]
            vals = [row[s] for s in stats] + [row[stats[0]]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=stats + [stats[0]], fill="toself", name=name,
                line_color=palette[i % len(palette)],
            ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="#131F2E",
                radialaxis=dict(visible=True, range=[0, 260],
                                gridcolor=WESCO_BORDER, color=WESCO_MUTED),
                angularaxis=dict(gridcolor=WESCO_BORDER, color=WESCO_TEXT),
            ),
            height=450,
            paper_bgcolor="rgba(0,0,0,0)",
            font_color=WESCO_TEXT,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Best Movesets
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💥 Best Movesets":
    st.title("Best Movesets")

    col1, col2, col3 = st.columns(3)
    stab_only = col1.checkbox("STAB moves only", value=False)
    dmg_class = col2.selectbox("Damage class", ["All", "physical", "special"])
    top_n     = col3.slider("Top N moves", 20, 200, 50)

    where_clauses = []
    if stab_only:
        where_clauses.append("is_stab = TRUE")
    if dmg_class != "All":
        where_clauses.append(f"damage_class = '{dmg_class}'")
    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    with st.spinner("Loading movesets…"):
        df = query(f"""
            SELECT pokemon_name, primary_type, move_name, move_type,
                   damage_class, power, accuracy, expected_damage, is_stab, move_rank
            FROM {CATALOG}.{SCHEMA}.mart_best_movesets
            {where}
            ORDER BY expected_damage DESC
            LIMIT {top_n}
        """)

    st.markdown("<div class='section-pill'>Expected Damage</div>", unsafe_allow_html=True)
    fig = px.bar(
        df, x="expected_damage", y="pokemon_name", orientation="h",
        color="move_type", color_discrete_map=TYPE_COLORS,
        hover_data=["move_name", "power", "accuracy", "damage_class", "is_stab"],
        labels={"expected_damage": "Expected Damage", "pokemon_name": ""},
    )
    fig.update_layout(height=max(400, top_n * 18), yaxis={"categoryorder": "total ascending"})
    apply_wesco_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-pill'>Power Distribution</div>", unsafe_allow_html=True)
    st.subheader("Move Power Distribution")
    df_dist = query(f"""
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
        FROM {CATALOG}.{SCHEMA}.dim_moves
        WHERE power IS NOT NULL AND damage_class IN ('physical', 'special')
        GROUP BY damage_class, power_bucket
        ORDER BY damage_class, power_bucket
    """)
    fig2 = px.bar(
        df_dist, x="power_bucket", y="move_count",
        color="damage_class", barmode="group",
        color_discrete_map={"physical": "#E74C3C", "special": WESCO_GREEN},
        labels={"power_bucket": "Power Range", "move_count": "# Moves"},
    )
    fig2.update_layout(height=350)
    apply_wesco_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Type Effectiveness
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔥 Type Effectiveness":
    st.title("Type Effectiveness Matrix")
    st.caption("How much damage does each attacking type deal to each defending type?")

    with st.spinner("Loading type chart…"):
        df = query(f"""
            SELECT attacking_type, defending_type, effectiveness_multiplier
            FROM {CATALOG}.{SCHEMA}.mart_type_effectiveness
            ORDER BY attacking_type, defending_type
        """)

    pivot = df.pivot(index="attacking_type", columns="defending_type", values="effectiveness_multiplier")
    fig = px.imshow(
        pivot,
        color_continuous_scale=[
            [0.0,  "#0D1B2A"],
            [0.25, "#7D0E0E"],
            [0.5,  "#1A2535"],
            [0.75, WESCO_GREEN_DARK],
            [1.0,  WESCO_GREEN],
        ],
        zmin=0, zmax=4, aspect="auto", text_auto=True,
        labels={"x": "Defending Type", "y": "Attacking Type", "color": "Multiplier"},
    )
    fig.update_layout(
        height=650,
        coloraxis_colorbar={"title": "Multiplier", "tickvals": [0, 0.5, 1, 2, 4]},
        xaxis={"tickangle": -45},
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=WESCO_TEXT,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("<div class='section-pill'>Single Type Drill-down</div>", unsafe_allow_html=True)
    all_types = sorted(df["attacking_type"].unique().tolist())
    chosen = st.selectbox(
        "Select attacking type", all_types,
        index=all_types.index("fire") if "fire" in all_types else 0,
    )
    df_single = df[df["attacking_type"] == chosen].sort_values("effectiveness_multiplier", ascending=False)
    fig2 = px.bar(
        df_single, x="defending_type", y="effectiveness_multiplier",
        color="defending_type", color_discrete_map=TYPE_COLORS,
        labels={"effectiveness_multiplier": "Multiplier", "defending_type": "Defending Type"},
    )
    fig2.add_hline(y=1, line_dash="dash", line_color=WESCO_MUTED, annotation_text="Neutral (1×)",
                   annotation_font_color=WESCO_MUTED)
    fig2.update_layout(height=350, showlegend=False)
    apply_wesco_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Stats by Type
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Stats by Type":
    st.title("Average Base Stats by Type")

    with st.spinner("Loading stats…"):
        df = query(f"""
            SELECT d.primary_type, v.stat_name,
                   ROUND(AVG(v.base_stat_value), 1) AS avg_base_stat
            FROM {CATALOG}.{SCHEMA}.fct_pokemon_stats f
            JOIN {CATALOG}.{SCHEMA}.dim_pokemon d ON f.pokemon_id = d.pokemon_id
            LATERAL VIEW explode(
                map(
                    'attack',           f.attack,
                    'defense',          f.defense,
                    'hp',               f.hp,
                    'speed',            f.speed,
                    'special-attack',   f.sp_attack,
                    'special-defense',  f.sp_defense
                )
            ) t AS stat_name, base_stat_value
            WHERE d.primary_type IS NOT NULL
              AND base_stat_value IS NOT NULL
            GROUP BY d.primary_type, v.stat_name
            ORDER BY d.primary_type, v.stat_name
        """)

    st.markdown("<div class='section-pill'>Avg Stats by Type</div>", unsafe_allow_html=True)
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
    apply_wesco_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-pill'>Attack vs Defense</div>", unsafe_allow_html=True)
    st.subheader("Attack vs Defense — All Pokémon")
    df_scatter = query(f"""
        SELECT d.pokemon_name, d.primary_type,
               f.attack, f.defense, f.hp, f.total_base_stats,
               d.is_legendary, d.is_mythical
        FROM {CATALOG}.{SCHEMA}.fct_pokemon_stats f
        JOIN {CATALOG}.{SCHEMA}.dim_pokemon d ON f.pokemon_id = d.pokemon_id
        WHERE f.attack IS NOT NULL AND f.defense IS NOT NULL
    """)

    show_legendary = st.checkbox("Highlight Legendaries", value=True)
    if show_legendary:
        df_scatter["category"] = df_scatter.apply(
            lambda r: "Mythical" if r["is_mythical"] else ("Legendary" if r["is_legendary"] else r["primary_type"]),
            axis=1,
        )
        color_col = "category"
        color_map = {**TYPE_COLORS, "Legendary": WESCO_GREEN, "Mythical": "#3498DB"}
    else:
        color_col = "primary_type"
        color_map = TYPE_COLORS

    fig2 = px.scatter(
        df_scatter, x="attack", y="defense",
        color=color_col, color_discrete_map=color_map,
        size="total_base_stats", hover_name="pokemon_name",
        hover_data=["hp", "total_base_stats"], opacity=0.75,
        labels={"attack": "Attack", "defense": "Defense"},
    )
    fig2.update_layout(height=500)
    apply_wesco_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)
