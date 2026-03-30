# Quick Start Deployment Guide

**Complete step-by-step instructions to deploy the Pokémon GO data pipeline**

⏱️ **Total Time**: ~2 hours (includes waiting for data sync)

---

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Snowflake account with admin access
- [ ] Access to the `jason_chletsos` database
- [ ] Your Snowflake private key file (e.g., `snowflake_key.p8`)
- [ ] Private key passphrase (if applicable)
- [ ] Fivetran account
- [ ] dbt Cloud account
- [ ] Git repository access (this repo)

---

## Part 1: Snowflake Setup (15 minutes)

### Step 1.1: Verify Your Key Pair Authentication

Open Snowflake and run:

```sql
-- Check your user has a public key registered
DESC USER <YOUR_USERNAME>;
```

✅ **Expected**: You should see `RSA_PUBLIC_KEY_FP` with a value  
❌ **If not**: Contact your Snowflake admin to register your public key

### Step 1.2: Create Schemas

```sql
-- Use the existing database
USE DATABASE jason_chletsos;

-- Create the three schemas we need
CREATE SCHEMA IF NOT EXISTS pokemon_raw
  COMMENT = 'Raw data from Fivetran PokéAPI connector';

CREATE SCHEMA IF NOT EXISTS pokemon_staging
  COMMENT = 'dbt staging models (views)';

CREATE SCHEMA IF NOT EXISTS pokemon_marts
  COMMENT = 'dbt marts models (tables)';

-- Verify they were created
SHOW SCHEMAS LIKE 'pokemon%';
```

✅ **Expected**: You should see 3 schemas: `pokemon_raw`, `pokemon_staging`, `pokemon_marts`

### Step 1.3: Verify Your Warehouse

```sql
-- Check what warehouses you have access to
SHOW WAREHOUSES;

-- Note the name of your default warehouse (you'll need this later)
```

✅ **Expected**: You should see at least one warehouse listed  
📝 **Note down**: Your warehouse name (e.g., `COMPUTE_WH`)

### Step 1.4: Grant Permissions for Fivetran

```sql
-- Replace FIVETRAN_ROLE with your actual Fivetran role name
-- Replace YOUR_WAREHOUSE with your warehouse name

GRANT USAGE ON DATABASE jason_chletsos TO ROLE FIVETRAN_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT CREATE TABLE ON SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT CREATE VIEW ON SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT USAGE ON WAREHOUSE YOUR_WAREHOUSE TO ROLE FIVETRAN_ROLE;
```

✅ **Expected**: All grants succeed with "Statement executed successfully"

### Step 1.5: Grant Permissions for dbt

```sql
-- Replace DBT_ROLE with your actual dbt role name
-- Replace YOUR_WAREHOUSE with your warehouse name

GRANT USAGE ON DATABASE jason_chletsos TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;

-- Read access to raw data
GRANT SELECT ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;

-- Full access to staging and marts
GRANT ALL ON SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;

GRANT USAGE ON WAREHOUSE YOUR_WAREHOUSE TO ROLE DBT_ROLE;
```

✅ **Expected**: All grants succeed

### Step 1.6: Verify Setup

```sql
-- Verify everything is set up correctly
USE DATABASE jason_chletsos;
SHOW SCHEMAS LIKE 'pokemon%';

-- Check grants
SHOW GRANTS TO ROLE FIVETRAN_ROLE;
SHOW GRANTS TO ROLE DBT_ROLE;
```

✅ **Checkpoint**: You should see all three schemas and proper grants

---

## Part 2: Deploy Fivetran Connector (30 minutes + sync time)

### Step 2.1: Package the Connector

Open your terminal and navigate to this project:

```bash
cd /Users/jason.chletsos/Documents/GitHub/jason-chletsos-fivetran-pogo
cd fivetran_pokemon_connector

# Create the connector package
zip -r pokemon_connector.zip connector.py requirements.txt configuration.json

# Verify the zip was created
ls -lh pokemon_connector.zip
```

✅ **Expected**: You should see `pokemon_connector.zip` (around 5-10 KB)

### Step 2.2: Log into Fivetran

1. Open your browser and go to https://fivetran.com
2. Log in with your credentials
3. You should see the Fivetran dashboard

### Step 2.3: Create a New Connector

1. Click **"+ Connector"** (top right)
2. In the search box, type **"Function"** or **"Custom Connector"**
3. Select **"Azure Function"** or **"AWS Lambda"** or **"Google Cloud Function"**
   - Choose based on your Fivetran plan
   - For testing, "Azure Function" is commonly available

### Step 2.4: Configure the Connector

**Connector Settings:**

| Field | Value |
|-------|-------|
| **Destination schema** | `pokemon_raw` |
| **Destination** | Select your Snowflake destination (or create new) |

Click **"Continue"**

### Step 2.5: Upload Connector Code

1. Click **"Upload Connector Package"**
2. Select the `pokemon_connector.zip` file you created
3. Wait for validation (30-60 seconds)

✅ **Expected**: "Validation successful" message

### Step 2.6: Configure Connector Parameters

You'll see a form with these fields (from `configuration.json`):

| Parameter | Value | Description |
|-----------|-------|-------------|
| `base_url` | `https://pokeapi.co/api/v2` | Leave default |
| `page_size` | `100` | Leave default |
| `pokemon_go_json_url` | `https://raw.githubusercontent.com/pokemongo-dev-contrib/pokemongo-json-pokedex/master/output/pokemon.json` | Leave default |

Click **"Save & Test"**

### Step 2.7: Configure Snowflake Destination

If you need to create a new Snowflake destination:

1. Click **"+ Add Destination"**
2. Select **"Snowflake"**
3. Fill in the connection details:

| Field | Your Value |
|-------|------------|
| **Host** | `<your_account>.snowflakecomputing.com` |
| **Port** | `443` |
| **Database** | `jason_chletsos` |
| **Schema** | `pokemon_raw` |
| **User** | Your Fivetran user |
| **Auth Method** | Password or Key Pair (based on your setup) |
| **Warehouse** | Your warehouse name |
| **Role** | Your Fivetran role |

4. Click **"Test Connection"**

✅ **Expected**: "Connection successful"

### Step 2.8: Start Initial Sync

1. Go back to your connector
2. Click **"Start Initial Sync"**
3. Monitor the sync progress

⏱️ **This will take 30-60 minutes** - the connector needs to fetch data for ~1,000 Pokémon

### Step 2.9: Monitor Sync Progress

While syncing, you'll see:
- **Status**: "Syncing"
- **Tables**: 8 tables being synced
- **Rows**: Increasing count

You can check Snowflake to see data arriving:

```sql
USE DATABASE jason_chletsos;
USE SCHEMA pokemon_raw;

-- Check what tables exist
SHOW TABLES;

-- Check row counts (will increase during sync)
SELECT 'pokemon' AS table_name, COUNT(*) AS row_count FROM pokemon
UNION ALL
SELECT 'pokemon_stats', COUNT(*) FROM pokemon_stats
UNION ALL
SELECT 'pokemon_types', COUNT(*) FROM pokemon_types
UNION ALL
SELECT 'pokemon_abilities', COUNT(*) FROM pokemon_abilities
UNION ALL
SELECT 'pokemon_moves', COUNT(*) FROM pokemon_moves
UNION ALL
SELECT 'types', COUNT(*) FROM types
UNION ALL
SELECT 'moves', COUNT(*) FROM moves
UNION ALL
SELECT 'species', COUNT(*) FROM species;
```

✅ **Expected final counts**:
- `pokemon`: ~1,000 rows
- `pokemon_stats`: ~6,000 rows
- `pokemon_types`: ~1,500 rows
- `pokemon_abilities`: ~3,000 rows
- `pokemon_moves`: ~50,000 rows
- `types`: ~20 rows
- `moves`: ~800 rows
- `species`: ~1,000 rows

### Step 2.10: Verify Sync Completion

Once sync completes:

```sql
-- Sample some data
SELECT * FROM pokemon LIMIT 10;
SELECT * FROM types;

-- Verify Fivetran metadata columns exist
SELECT 
    id,
    name,
    base_experience,
    _fivetran_synced
FROM pokemon
LIMIT 5;
```

✅ **Checkpoint**: Fivetran sync complete, data in Snowflake

---

## Part 3: Set Up dbt Cloud (30 minutes)

### Step 3.1: Log into dbt Cloud

1. Go to https://cloud.getdbt.com
2. Log in with your credentials

### Step 3.2: Create New Project

1. Click **"+ New Project"**
2. **Project Name**: `pokemon_go_dbt`
3. Click **"Continue"**

### Step 3.3: Connect to Snowflake

1. Select **"Snowflake"** as your data platform
2. Fill in connection details:

| Field | Your Value |
|-------|------------|
| **Account** | Your Snowflake account (e.g., `abc12345.us-east-1`) |
| **Role** | Your dbt role |
| **Warehouse** | Your warehouse name |
| **Database** | `jason_chletsos` |
| **Schema** | `pokemon_raw` |

3. **Authentication**: Select **"Key Pair"**
   - **Username**: Your Snowflake username
   - **Private Key**: Upload your `snowflake_key.p8` file
   - **Passphrase**: Enter your passphrase (if applicable)

4. Click **"Test Connection"**

✅ **Expected**: "Connection test succeeded"

### Step 3.4: Connect to Git Repository

1. In Project Settings, go to **"Repository"**
2. Click **"Git Clone"** or **"Connect GitHub"**
3. Select **GitHub** (or your Git provider)
4. Authorize dbt Cloud to access your repositories
5. Select this repository: `jason-chletsos-fivetran-pogo`
6. **Project subdirectory**: `dbt_pokemon_go/`
7. Click **"Save"**

✅ **Expected**: "Repository connected successfully"

### Step 3.5: Set Up Development Environment

1. Go to **"Environments"**
2. Click **"Create Environment"**
3. Configure:

| Field | Value |
|-------|-------|
| **Name** | `Development` |
| **Environment Type** | Development |
| **dbt Version** | Latest (e.g., `1.7`) |
| **Deployment Credentials** | Use project connection |

4. Click **"Save"**

### Step 3.6: Set Up Production Environment

1. Click **"Create Environment"** again
2. Configure:

| Field | Value |
|-------|-------|
| **Name** | `Production` |
| **Environment Type** | Deployment |
| **dbt Version** | Latest (e.g., `1.7`) |
| **Deployment Credentials** | Use project connection |

3. Click **"Save"**

### Step 3.7: Open dbt Cloud IDE

1. Click **"Develop"** in the top menu
2. Select your **Development** environment
3. Wait for IDE to load

### Step 3.8: Install Dependencies

In the dbt Cloud IDE command line (bottom panel), run:

```bash
dbt deps
```

✅ **Expected**: 
```
Installing dbt-utils
Installed 1 package
```

### Step 3.9: Test Connection

```bash
dbt debug
```

✅ **Expected**:
```
Connection test: [OK connection ok]
```

### Step 3.10: Run dbt Models

```bash
# Run all models
dbt run
```

⏱️ **This takes 2-5 minutes**

✅ **Expected output**:
```
Completed successfully

Done. PASS=15 WARN=0 ERROR=0 SKIP=0 TOTAL=15
```

You should see:
- 8 staging models (views)
- 7 marts models (tables)

### Step 3.11: Run dbt Tests

```bash
dbt test
```

✅ **Expected**:
```
Completed successfully

Done. PASS=25 WARN=0 ERROR=0 SKIP=0 TOTAL=25
```

### Step 3.12: Verify Models in Snowflake

Go back to Snowflake and check:

```sql
-- Check staging views
USE SCHEMA pokemon_staging;
SHOW VIEWS;
SELECT COUNT(*) FROM stg_pokemon;

-- Check marts tables
USE SCHEMA pokemon_marts;
SHOW TABLES;

-- Sample the marts
SELECT * FROM mart_top_attackers LIMIT 10;
SELECT * FROM mart_top_defenders LIMIT 10;
SELECT * FROM mart_legendary_rankings LIMIT 10;
```

✅ **Checkpoint**: dbt models built successfully

---

## Part 4: Set Up Orchestration (15 minutes)

### Step 4.1: Create dbt Cloud Job

1. In dbt Cloud, go to **"Deploy"** → **"Jobs"**
2. Click **"Create Job"**
3. Configure:

| Field | Value |
|-------|-------|
| **Job Name** | `Daily Pokemon Refresh` |
| **Environment** | Production |
| **Commands** | `dbt run`<br>`dbt test` |
| **Triggers** | Webhook |

4. Click **"Save"**

### Step 4.2: Get Webhook URL

1. In the job settings, find **"Webhooks"** section
2. Click **"Create Webhook"**
3. **Webhook Name**: `Fivetran Trigger`
4. Copy the webhook URL (you'll need this)

Example: `https://cloud.getdbt.com/api/v2/accounts/12345/jobs/67890/run/`

### Step 4.3: Get dbt Cloud API Token

1. Click your profile icon (top right)
2. Go to **"Account Settings"** → **"API Access"**
3. Click **"Create Token"**
4. **Token Name**: `Fivetran Integration`
5. **Permissions**: Select **"Job Admin"**
6. Copy the token (save it securely!)

### Step 4.4: Configure Fivetran Webhook

1. Go back to Fivetran
2. Open your Pokemon connector
3. Go to **"Setup"** tab
4. Scroll to **"Webhooks"** section
5. Click **"Add Webhook"**
6. Configure:

| Field | Value |
|-------|-------|
| **Webhook URL** | Paste your dbt Cloud webhook URL |
| **Secret** | Paste your dbt Cloud API token |
| **Event** | `sync_end` |

7. Click **"Save"**

### Step 4.5: Test the Webhook

1. In Fivetran, click **"Test Webhook"**
2. Check dbt Cloud for a new job run

✅ **Expected**: You should see a new run appear in dbt Cloud

### Step 4.6: Test End-to-End Pipeline

Trigger a manual sync in Fivetran:

1. Go to your connector
2. Click **"Sync Now"**
3. Wait for sync to complete
4. Check dbt Cloud - a new job should automatically start

✅ **Expected**: 
- Fivetran sync completes
- dbt Cloud job starts automatically
- dbt job completes successfully

---

## Part 5: Verify Everything Works (10 minutes)

### Step 5.1: Check Data Freshness

```sql
USE DATABASE jason_chletsos;
USE SCHEMA pokemon_marts;

-- Check when data was last updated
SELECT 
    'dim_pokemon' AS table_name,
    COUNT(*) AS row_count,
    MAX(_fivetran_synced) AS last_synced
FROM dim_pokemon
UNION ALL
SELECT 
    'fct_pokemon_stats',
    COUNT(*),
    MAX(synced_at)
FROM fct_pokemon_stats;
```

✅ **Expected**: Recent timestamps (within last hour)

### Step 5.2: Run Sample Queries

```sql
-- Top 10 attackers
SELECT 
    pokemon_name,
    attack,
    tier,
    type_1,
    type_2
FROM mart_top_attackers
WHERE tier = 'S'
ORDER BY overall_rank
LIMIT 10;

-- Best movesets for Charizard
SELECT 
    pokemon_name,
    move_name,
    move_power,
    move_type,
    move_rank
FROM mart_best_movesets
WHERE pokemon_name = 'charizard'
ORDER BY move_rank;

-- Type effectiveness
SELECT 
    attacking_type,
    defending_type,
    effectiveness_multiplier
FROM mart_type_effectiveness
WHERE attacking_type = 'fire'
ORDER BY effectiveness_multiplier DESC;
```

✅ **Expected**: Meaningful results with Pokemon data

### Step 5.3: Check Fivetran Sync Schedule

1. In Fivetran, go to your connector
2. Check **"Sync Frequency"**
3. Recommended: **Daily** at a time that works for you

### Step 5.4: Set Up Monitoring

**Fivetran Alerts:**
1. Go to **"Notifications"** in Fivetran
2. Enable alerts for:
   - ❌ Sync failures
   - ⚠️ Sync delays

**dbt Cloud Alerts:**
1. Go to your job settings
2. Click **"Notifications"**
3. Add your email
4. Enable alerts for:
   - ❌ Job failures
   - ⚠️ Test failures

---

## 🎉 Deployment Complete!

### What You've Built

✅ **Data Pipeline**:
- Fivetran connector syncing 1,000+ Pokemon from PokéAPI
- 8 raw tables in Snowflake
- 8 staging models (views)
- 7 marts models (tables)

✅ **Orchestration**:
- Automatic dbt runs after Fivetran syncs
- Daily refresh schedule

✅ **Analytics Ready**:
- Battle strategy insights
- Type effectiveness matrices
- Moveset recommendations
- Legendary rankings

### Next Steps

1. **Build Dashboards**: Connect Tableau/PowerBI/Looker to the marts
2. **Add More Data**: Integrate PvPoke data for competitive rankings
3. **Create Alerts**: Set up data quality monitors
4. **Share Insights**: Query the marts for battle strategies

### Quick Reference

| Component | Location |
|-----------|----------|
| **Raw Data** | `jason_chletsos.pokemon_raw.*` |
| **Staging Views** | `jason_chletsos.pokemon_staging.stg_*` |
| **Marts Tables** | `jason_chletsos.pokemon_marts.mart_*` |
| **Fivetran Connector** | Fivetran dashboard |
| **dbt Project** | dbt Cloud IDE |
| **Documentation** | See README.md files |

### Troubleshooting

If something went wrong, check:
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed troubleshooting section
- [KEY_PAIR_AUTH_SETUP.md](./KEY_PAIR_AUTH_SETUP.md) - Authentication issues
- Fivetran logs - In connector → Logs tab
- dbt Cloud logs - In job run details

### Support

- **Fivetran**: https://fivetran.com/docs
- **dbt**: https://docs.getdbt.com
- **Snowflake**: https://docs.snowflake.com

---

**Congratulations! Your Pokemon GO data pipeline is live! 🚀**
