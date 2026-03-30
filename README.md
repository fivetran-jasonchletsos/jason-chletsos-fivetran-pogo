# Pokémon GO Data Pipeline

**Complete end-to-end data pipeline for Pokémon battle analytics**

Fivetran Custom Connector → Snowflake → dbt Cloud → Battle-Ready Analytics

---

## 🎯 Project Overview

This project provides a production-ready data pipeline that:

1. **Extracts** Pokémon data from PokéAPI using a custom Fivetran connector
2. **Loads** raw data into Snowflake (`POKEMON_RAW` schema)
3. **Transforms** data using dbt Cloud into clean, analytical models
4. **Delivers** battle strategy insights via marts optimized for Pokémon GO gameplay

### What You Get

- **1,000+** Pokémon with complete stats, types, abilities, and movesets
- **800+** Moves with power, accuracy, and type effectiveness data
- **18** Type matchup matrices for strategic planning
- **Pre-built marts** answering key battle questions:
  - Which Pokémon are the best attackers?
  - Which Pokémon make the best gym defenders?
  - What moves should each Pokémon use?
  - How do types interact in battle?
  - Which legendary Pokémon are the strongest?

---

## 📁 Project Structure

```
jason-chletsos-fivetran-pogo/
├── README.md                          # This file
├── DEPLOYMENT.md                      # Complete deployment guide
├── KEY_PAIR_AUTH_SETUP.md            # Key pair authentication guide
│
├── fivetran_pokemon_connector/        # Fivetran custom connector
│   ├── connector.py                   # Main connector logic
│   ├── requirements.txt               # Python dependencies
│   ├── configuration.json             # Connector configuration
│   ├── debug.py                       # Local testing script
│   └── README.md                      # Connector documentation
│
└── dbt_pokemon_go/                    # dbt Cloud project
    ├── dbt_project.yml                # dbt project config
    ├── profiles.yml                   # Snowflake connection template
    ├── packages.yml                   # dbt dependencies
    ├── README.md                      # dbt project documentation
    │
    ├── models/
    │   ├── sources.yml                # Source definitions
    │   │
    │   ├── staging/                   # Staging models (views)
    │   │   ├── staging.yml            # Model documentation + tests
    │   │   ├── stg_pokemon.sql
    │   │   ├── stg_pokemon_stats.sql
    │   │   ├── stg_pokemon_types.sql
    │   │   ├── stg_pokemon_abilities.sql
    │   │   ├── stg_pokemon_moves.sql
    │   │   ├── stg_types.sql
    │   │   ├── stg_moves.sql
    │   │   └── stg_species.sql
    │   │
    │   └── marts/                     # Marts models (tables)
    │       ├── marts.yml              # Model documentation + tests
    │       ├── dim_pokemon.sql        # Pokémon dimension
    │       ├── dim_moves.sql          # Moves dimension
    │       ├── fct_pokemon_stats.sql  # Stats fact table
    │       ├── mart_top_attackers.sql # Best offensive Pokémon
    │       ├── mart_top_defenders.sql # Best defensive Pokémon
    │       ├── mart_type_effectiveness.sql # Type matchup matrix
    │       ├── mart_best_movesets.sql # Optimal moves per Pokémon
    │       └── mart_legendary_rankings.sql # Legendary tier list
    │
    └── macros/
        └── generate_schema_name.sql   # Schema routing logic
```

---

## 🚀 Quick Start

### Prerequisites

- **Snowflake account** (trial or paid)
- **Fivetran account** with custom connector support
- **dbt Cloud account** (or dbt Core installed locally)
- **Git** for version control

### Deployment Steps

**Full deployment takes ~2 hours** (mostly waiting for initial data sync)

1. **Set up Snowflake** (15 minutes)
   - Create database and schemas
   - Configure key pair authentication
   - Grant permissions to roles
   - See: [DEPLOYMENT.md - Section 1](./DEPLOYMENT.md#1-snowflake-setup)
   - **Auth Setup**: [KEY_PAIR_AUTH_SETUP.md](./KEY_PAIR_AUTH_SETUP.md)

2. **Deploy Fivetran Connector** (30 minutes + 30-60 min sync time)
   - Package and upload custom connector
   - Configure Snowflake destination
   - Run initial sync
   - See: [DEPLOYMENT.md - Section 2](./DEPLOYMENT.md#2-fivetran-custom-connector-deployment)

3. **Set up dbt Cloud** (30 minutes)
   - Create project and connect to Snowflake with key pair auth
   - Connect to Git repository
   - Install dependencies and run models
   - See: [DEPLOYMENT.md - Section 3](./DEPLOYMENT.md#3-dbt-cloud-project-setup)

4. **Configure Orchestration** (15 minutes)
   - Set up Fivetran → dbt Cloud webhook
   - Test end-to-end pipeline
   - See: [DEPLOYMENT.md - Section 4](./DEPLOYMENT.md#4-orchestration-configuration)

**📖 Detailed instructions**: See [DEPLOYMENT.md](./DEPLOYMENT.md)  
**🔐 Key Pair Auth Guide**: See [KEY_PAIR_AUTH_SETUP.md](./KEY_PAIR_AUTH_SETUP.md)

---

## 🏗️ Architecture

```
┌─────────────────┐
│    PokéAPI      │  Free public API (no auth required)
│  pokeapi.co     │  ~1,000 Pokémon, 800+ moves, type data
└────────┬────────┘
         │
         │ HTTPS requests with pagination
         │ Exponential backoff retry logic
         │
┌────────▼────────────────────────────────────────┐
│   Fivetran Custom Connector (Python)            │
│   - Extracts data from PokéAPI                  │
│   - Handles pagination, rate limits, errors     │
│   - Incremental sync with cursor tracking       │
└────────┬────────────────────────────────────────┘
         │
         │ Bulk insert via Snowflake connector
         │
┌────────▼────────────────────────────────────────┐
│   Snowflake - jason_chletsos.pokemon_raw            │
│   - pokemon (1,000 rows)                        │
│   - pokemon_stats (6,000 rows)                  │
│   - pokemon_types (1,500 rows)                  │
│   - pokemon_abilities (3,000 rows)              │
│   - pokemon_moves (50,000 rows)                 │
│   - types (20 rows)                             │
│   - moves (800 rows)                            │
│   - species (1,000 rows)                        │
└────────┬────────────────────────────────────────┘
         │
         │ Webhook triggers dbt Cloud job
         │
┌────────▼────────────────────────────────────────┐
│   dbt Cloud Transformations                     │
│   - Staging models (views in POKEMON_STAGING)   │
│   - Marts models (tables in POKEMON_MARTS)      │
│   - Data quality tests                          │
└────────┬────────────────────────────────────────┘
         │
         │
┌────────▼────────────────────────────────────────┐
│   Snowflake - jason_chletsos.pokemon_marts          │
│   - dim_pokemon                                 │
│   - dim_moves                                   │
│   - fct_pokemon_stats                           │
│   - mart_top_attackers                          │
│   - mart_top_defenders                          │
│   - mart_type_effectiveness                     │
│   - mart_best_movesets                          │
│   - mart_legendary_rankings                     │
└────────┬────────────────────────────────────────┘
         │
         │ SQL queries
         │
┌────────▼────────────────────────────────────────┐
│   Analytics & Visualization                     │
│   - Tableau / Looker / Power BI dashboards      │
│   - Direct SQL queries                          │
│   - Custom applications                         │
└─────────────────────────────────────────────────┘
```

---

## 📊 Data Models

### Staging Layer (Views in `POKEMON_STAGING`)

Clean, typed versions of raw Fivetran data:

- `stg_pokemon` — Core Pokémon attributes
- `stg_pokemon_stats` — Individual stat values (HP, Attack, Defense, etc.)
- `stg_pokemon_types` — Type assignments (Fire, Water, etc.)
- `stg_pokemon_abilities` — Ability assignments
- `stg_pokemon_moves` — Move learnsets
- `stg_types` — Type effectiveness data
- `stg_moves` — Move details
- `stg_species` — Species-level data (legendary status, generation, etc.)

### Marts Layer (Tables in `POKEMON_MARTS`)

#### Dimensions
- **`dim_pokemon`** — Wide Pokémon dimension with types, species data, physical attributes
- **`dim_moves`** — Enriched moves with calculated expected damage

#### Facts
- **`fct_pokemon_stats`** — Pokémon stats pivoted into columns with total base stats

#### Business Marts

**`mart_top_attackers`** — Best offensive Pokémon ranked by Attack stat
- Tier classifications: S (250+), A (200+), B (150+), C (<150)
- Separate rankings for legendary vs non-legendary
- Use case: *"Which Pokémon should I power up for raids?"*

**`mart_top_defenders`** — Best defensive Pokémon ranked by Defense + HP
- Tier classifications: S (350+), A (300+), B (250+), C (<250)
- Use case: *"Which Pokémon should I leave in gyms?"*

**`mart_type_effectiveness`** — Type matchup matrix
- Effectiveness multipliers: 2.0 (super effective), 1.0 (normal), 0.5 (not very effective), 0.0 (no effect)
- Use case: *"What type should I use against this gym defender?"*

**`mart_best_movesets`** — Top 3 moves per Pokémon by power
- Includes STAB (Same Type Attack Bonus) indicators
- Expected damage calculations (power × accuracy)
- Use case: *"What moves should I teach my Pokémon?"*

**`mart_legendary_rankings`** — Legendary/mythical Pokémon tier list
- Ranked by total base stats
- Separated into Legendary vs Mythical tiers
- Use case: *"Which legendary should I prioritize catching?"*

---

## 💡 Usage Examples

### Query: Top 10 Non-Legendary Attackers

```sql
SELECT 
    pokemon_name,
    primary_type,
    secondary_type,
    attack,
    tier
FROM jason_chletsos.pokemon_marts.MART_TOP_ATTACKERS
WHERE is_legendary = FALSE
ORDER BY overall_rank
LIMIT 10;
```

### Query: Best Defenders Against Fire Attacks

```sql
SELECT 
    d.pokemon_name,
    d.primary_type,
    d.secondary_type,
    d.combined_defensive_stat,
    d.tier
FROM jason_chletsos.pokemon_marts.MART_TOP_DEFENDERS d
JOIN jason_chletsos.pokemon_marts.MART_TYPE_EFFECTIVENESS e
    ON d.primary_type = e.defending_type
WHERE e.attacking_type = 'fire'
    AND e.effectiveness_multiplier <= 0.5
ORDER BY d.combined_defensive_stat DESC
LIMIT 10;
```

### Query: Best Moveset for Charizard

```sql
SELECT 
    move_name,
    move_type,
    power,
    accuracy,
    is_stab,
    move_rank
FROM jason_chletsos.pokemon_marts.MART_BEST_MOVESETS
WHERE pokemon_name = 'charizard'
ORDER BY move_rank;
```

### Query: Top 20 Legendary Pokémon

```sql
SELECT 
    pokemon_name,
    rarity_tier,
    total_base_stats,
    attack,
    defense,
    speed,
    overall_rank
FROM jason_chletsos.pokemon_marts.MART_LEGENDARY_RANKINGS
ORDER BY total_base_stats DESC
LIMIT 20;
```

---

## 🔧 Maintenance & Monitoring

### Automated Pipeline

Once deployed, the pipeline runs automatically:

1. **Fivetran syncs daily** at 1:00 AM (configurable)
2. **Webhook triggers dbt Cloud** immediately after sync completes
3. **dbt transforms data** in ~2-5 minutes
4. **Fresh data available** in `POKEMON_MARTS` by ~1:35 AM

### Monitoring

**Fivetran Dashboard**:
- Sync status (should be "Succeeded")
- Rows synced per table
- API errors (should be 0)

**dbt Cloud Dashboard**:
- Job run status (should be "Success")
- Test results (should all pass)
- Model build times

**Snowflake**:
- Warehouse credit usage
- Query performance
- Data freshness

See [DEPLOYMENT.md - Section 6](./DEPLOYMENT.md#6-monitoring--maintenance) for detailed monitoring setup.

---

## 🧪 Testing

### Local Testing (Fivetran Connector)

```bash
cd fivetran_pokemon_connector
pip install -r requirements.txt
python debug.py
```

This runs a simulated sync and outputs results to console.

### dbt Testing

```bash
cd dbt_pokemon_go

# Install dependencies
dbt deps

# Run models
dbt run

# Run tests
dbt test

# Run specific model
dbt run --select mart_top_attackers

# Test specific model
dbt test --select mart_top_attackers
```

### End-to-End Testing

1. Trigger Fivetran sync manually
2. Verify webhook triggers dbt job
3. Run validation queries in Snowflake (see [DEPLOYMENT.md - Section 5](./DEPLOYMENT.md#5-validation--testing))

---

## 📈 Performance

### Data Volume

| Schema | Objects | Total Rows | Storage |
|--------|---------|------------|---------|
| `POKEMON_RAW` | 8 tables | ~62,000 | ~10 MB |
| `POKEMON_STAGING` | 8 views | ~62,000 | 0 MB (views) |
| `POKEMON_MARTS` | 7 tables | ~65,000 | ~15 MB |

### Sync Times

- **Initial Fivetran sync**: 30-60 minutes (depends on API response times)
- **Incremental Fivetran sync**: 5-15 minutes (only new/changed Pokémon)
- **dbt transformation**: 2-5 minutes

### Query Performance

All mart queries return in **< 1 second** on XSMALL warehouse.

---

## 🔐 Security

### Credentials Management

- **Snowflake passwords**: Stored securely in Fivetran and dbt Cloud
- **API keys**: Not required (PokéAPI is public)
- **dbt Cloud API token**: Used only for webhook authentication

### Permissions

- **Fivetran role**: Read/write access to `POKEMON_RAW` only
- **dbt role**: Read access to `POKEMON_RAW`, full access to `POKEMON_STAGING` and `POKEMON_MARTS`
- **Principle of least privilege** enforced throughout

See [DEPLOYMENT.md - Section 1.3](./DEPLOYMENT.md#13-create-roles-and-grant-permissions) for detailed permission setup.

---

## 🛠️ Customization

### Adding New Marts

1. Create new `.sql` file in `dbt_pokemon_go/models/marts/`
2. Add documentation in `marts.yml`
3. Run `dbt run --select +your_new_mart`
4. Add tests in `marts.yml`
5. Commit and push to Git

### Modifying Tier Thresholds

Edit tier logic in mart models (e.g., `mart_top_attackers.sql`):

```sql
case
    when ps.attack >= 250 then 'S'  -- Change these thresholds
    when ps.attack >= 200 then 'A'
    when ps.attack >= 150 then 'B'
    else 'C'
end as tier
```

### Adding New Data Sources

To add PvPoke data or Pokémon GO Gamemaster JSON:

1. Extend Fivetran connector to fetch additional endpoints
2. Add new source tables in `sources.yml`
3. Create staging models for new sources
4. Join with existing marts or create new ones

---

## 📚 Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** — Complete deployment guide with step-by-step instructions
- **[fivetran_pokemon_connector/README.md](./fivetran_pokemon_connector/README.md)** — Fivetran connector documentation
- **[dbt_pokemon_go/README.md](./dbt_pokemon_go/README.md)** — dbt project documentation with model descriptions

---

## 🐛 Troubleshooting

### Common Issues

**Fivetran sync fails with "Rate limit exceeded"**
- Solution: Increase `page_size` or decrease sync frequency

**dbt job fails with "Schema does not exist"**
- Solution: Verify schemas exist in Snowflake and permissions are granted

**Webhook not triggering dbt job**
- Solution: Verify API token, job ID, and webhook configuration

**Queries are slow**
- Solution: Add clustering, increase warehouse size, or enable result caching

See [DEPLOYMENT.md - Section 6.5](./DEPLOYMENT.md#65-troubleshooting-common-issues) for detailed troubleshooting.

---

## 🤝 Contributing

This project is provided as-is for educational purposes. Feel free to:

- Fork and customize for your own use
- Add new marts or data sources
- Optimize performance
- Share improvements

---

## 📄 License

This project is provided as-is for educational and analytical purposes.

Pokémon data is sourced from [PokéAPI](https://pokeapi.co), which aggregates data from various Pokémon games and media. Pokémon and Pokémon character names are trademarks of Nintendo, Game Freak, and The Pokémon Company.

---

## 🔗 Resources

- **PokéAPI Documentation**: https://pokeapi.co/docs/v2
- **Fivetran Documentation**: https://fivetran.com/docs
- **Fivetran Connector SDK**: https://github.com/fivetran/fivetran_connector_sdk
- **dbt Documentation**: https://docs.getdbt.com
- **Snowflake Documentation**: https://docs.snowflake.com
- **Pokémon GO Hub**: https://pokemongohub.net (for game mechanics)
- **PvPoke**: https://pvpoke.com (for PvP rankings)

---

## 🎮 Next Steps

After deploying this pipeline, consider:

1. **Build a dashboard** in Tableau, Looker, or Power BI
2. **Add PvP data** from PvPoke for Great League, Ultra League, Master League rankings
3. **Integrate Pokémon GO Gamemaster** for CP calculations and raid boss data
4. **Create a web app** that recommends teams based on gym defenders
5. **Add weather boost** calculations for Pokémon GO mechanics
6. **Build a raid counter tool** that suggests optimal attackers for each raid boss

---

**Built with ❤️ for Pokémon trainers and data engineers**

Ready to catch 'em all? Start with [DEPLOYMENT.md](./DEPLOYMENT.md)!
