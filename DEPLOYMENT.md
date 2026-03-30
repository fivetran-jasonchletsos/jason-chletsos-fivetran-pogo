# Deployment Guide: Pokémon GO Data Pipeline

Complete end-to-end deployment instructions for the Fivetran → Snowflake → dbt Cloud pipeline.

---

## Table of Contents

1. [Snowflake Setup](#1-snowflake-setup)
2. [Fivetran Custom Connector Deployment](#2-fivetran-custom-connector-deployment)
3. [dbt Cloud Project Setup](#3-dbt-cloud-project-setup)
4. [Orchestration Configuration](#4-orchestration-configuration)
5. [Validation & Testing](#5-validation--testing)
6. [Monitoring & Maintenance](#6-monitoring--maintenance)

---

## 1. Snowflake Setup

### 1.1 Create Schemas

Log into Snowflake and run the following SQL commands:

```sql
-- Use existing database
USE DATABASE jason_chletsos;

-- Create schemas for the pipeline
CREATE SCHEMA IF NOT EXISTS pokemon_raw
  COMMENT = 'Raw data from Fivetran PokéAPI connector';

CREATE SCHEMA IF NOT EXISTS pokemon_staging
  COMMENT = 'dbt staging models (views)';

CREATE SCHEMA IF NOT EXISTS pokemon_marts
  COMMENT = 'dbt marts models (tables)';

-- Verify default warehouse is available
SHOW WAREHOUSES;
```

### 1.2 Configure Key Pair Authentication

Your Snowflake users should already have RSA key pairs configured. Verify this:

```sql
-- Verify public key is registered for your dbt user
DESC USER <YOUR_DBT_USERNAME>;
-- Look for RSA_PUBLIC_KEY_FP (fingerprint) in the output

-- If not set, contact your Snowflake admin to register your public key
```

**Locate your private key file:**
- Your private key should be stored securely (e.g., `~/.ssh/snowflake_key.p8`)
- You'll need the path to this file for dbt configuration
- If your key has a passphrase, keep it ready

### 1.3 Grant Permissions

#### For Fivetran

```sql
-- Grant permissions to your Fivetran user/role
-- Replace FIVETRAN_ROLE with your actual Fivetran role

GRANT USAGE ON DATABASE jason_chletsos TO ROLE FIVETRAN_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT CREATE TABLE ON SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT CREATE VIEW ON SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;

-- Grant permissions on all tables in the schema (for updates)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE FIVETRAN_ROLE;

-- Grant warehouse permissions (use default warehouse)
GRANT USAGE ON WAREHOUSE <YOUR_DEFAULT_WAREHOUSE> TO ROLE FIVETRAN_ROLE;
```

#### For dbt Cloud

```sql
-- Grant permissions to your dbt user/role
-- Replace DBT_ROLE with your actual dbt role

GRANT USAGE ON DATABASE jason_chletsos TO ROLE DBT_ROLE;

-- Grant schema permissions
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;

-- Grant read access to raw data
GRANT SELECT ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;

-- Grant full access to staging and marts schemas
GRANT ALL ON SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;

-- Grant warehouse permissions (use default warehouse)
GRANT USAGE ON WAREHOUSE <YOUR_DEFAULT_WAREHOUSE> TO ROLE DBT_ROLE;
```

### 1.4 Verify Setup

```sql
-- Verify database exists
SHOW DATABASES LIKE 'jason_chletsos';

-- Verify schemas exist
USE DATABASE jason_chletsos;
SHOW SCHEMAS LIKE 'pokemon%';

-- Verify warehouse exists
SHOW WAREHOUSES;

-- Verify your roles have proper permissions
SHOW GRANTS TO ROLE FIVETRAN_ROLE;
SHOW GRANTS TO ROLE DBT_ROLE;

-- Verify key pair authentication is configured
DESC USER <YOUR_DBT_USERNAME>;
-- Confirm RSA_PUBLIC_KEY_FP is present
```

---

## 2. Fivetran Custom Connector Deployment

### 2.1 Package the Connector

From the project root:

```bash
cd fivetran_pokemon_connector
zip -r pokemon_connector.zip connector.py requirements.txt configuration.json
```

### 2.2 Upload to Fivetran

1. Log into your Fivetran account at https://fivetran.com
2. Navigate to **Connectors** → **+ Connector**
3. Search for **"Custom Connector"** or **"Python Connector"**
4. Click **"Set Up"**

### 2.3 Configure the Connector

#### Basic Configuration

- **Connector Name**: `pokemon_pokeapi`
- **Destination**: Select your Snowflake destination (or create a new one)
- **Schema**: `pokemon_raw` (in the `jason_chletsos` database)

#### Upload Connector Code

1. Click **"Upload Connector Package"**
2. Select the `pokemon_connector.zip` file
3. Wait for validation to complete

#### Connector Settings

Configure these parameters (or leave defaults):

```json
{
  "base_url": "https://pokeapi.co/api/v2",
  "page_size": 100,
  "pokemon_go_json_url": "https://raw.githubusercontent.com/pokemongo-dev-contrib/pokemongo-json-pokedex/master/output/pokemon.json"
}
```

#### Snowflake Destination Configuration

If creating a new Snowflake destination:

1. **Host**: `<your_account>.snowflakecomputing.com`
2. **Port**: `443`
3. **Database**: `jason_chletsos`
4. **Schema**: `pokemon_raw`
5. **User**: Your Fivetran user
6. **Password**: Your Fivetran user password
7. **Warehouse**: Your default warehouse
8. **Role**: Your Fivetran role

### 2.4 Test Connection

1. Click **"Test Connection"**
2. Verify all checks pass:
   - ✅ Connection to Snowflake successful
   - ✅ Schema accessible
   - ✅ Connector code validated
   - ✅ API accessible (PokéAPI)

### 2.5 Configure Sync Settings

#### Sync Frequency

**Recommended**: **Daily** at 1:00 AM (your timezone)

Rationale: PokéAPI data is mostly static. Daily sync is sufficient and avoids unnecessary API calls.

**For Testing**: Set to **Hourly** initially to verify the pipeline works, then change to daily.

#### Sync Mode

- **Mode**: Full table sync (default for custom connectors)
- **Incremental**: Enabled automatically for `pokemon` table via cursor

### 2.6 Run Initial Sync

1. Click **"Start Initial Sync"**
2. Monitor progress in the Fivetran dashboard
3. Expected duration: **30-60 minutes** (depends on API response times)

#### What to Expect

The connector will sync these tables to `jason_chletsos.pokemon_raw`:

| Table | Approximate Rows |
|-------|------------------|
| `pokemon` | ~1,000 |
| `pokemon_stats` | ~6,000 |
| `pokemon_types` | ~1,500 |
| `pokemon_abilities` | ~3,000 |
| `pokemon_moves` | ~50,000 |
| `types` | ~20 |
| `moves` | ~800 |
| `species` | ~1,000 |

### 2.7 Verify Data in Snowflake

After the sync completes, run these queries in Snowflake:

```sql
USE DATABASE jason_chletsos;
USE SCHEMA pokemon_raw;

-- Check row counts
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

-- Sample data from pokemon table
SELECT * FROM pokemon LIMIT 10;

-- Verify Fivetran metadata columns exist
SELECT 
    id,
    name,
    _fivetran_synced
FROM pokemon
LIMIT 5;
```

---

## 3. dbt Cloud Project Setup

### 3.1 Create dbt Cloud Project

1. Log into dbt Cloud at https://cloud.getdbt.com
2. Click **"New Project"**
3. **Project Name**: `pokemon_go_dbt`
4. Click **"Continue"**

### 3.2 Connect to Snowflake

1. In the project setup wizard, select **"Snowflake"** as your data warehouse
2. Configure connection settings:

   - **Account**: Your Snowflake account identifier
     - Format: `<account_locator>.<region>` (e.g., `abc12345.us-east-1`)
     - Find this in Snowflake: `SELECT CURRENT_ACCOUNT();`
   
   - **Role**: Your dbt role
   - **Warehouse**: Your default warehouse
   - **Database**: `jason_chletsos`
   - **Schema**: `pokemon_raw` (default, will be overridden by models)

3. **Authentication**: Key Pair Authentication (Recommended)

   - **Username**: Your Snowflake username
   - **Authentication Method**: Select **"Key Pair"**
   - **Private Key**: Upload your `snowflake_key.p8` file
   - **Private Key Passphrase**: Enter the passphrase you used when generating the key

4. Click **"Test Connection"**
5. Verify connection succeeds

### 3.3 Connect to Git Repository

1. In dbt Cloud, go to **Project Settings → Repository**
2. Choose your Git provider (GitHub, GitLab, Bitbucket, etc.)
3. Authorize dbt Cloud to access your repository
4. Select the repository containing this project
5. **Project Subdirectory**: `dbt_pokemon_go/` (if this is part of a larger repo)
6. Click **"Save"**

### 3.4 Set Up Environments

#### Development Environment

1. Go to **Environments** → **Create Environment**
2. **Name**: `Development`
3. **Environment Type**: Development
4. **dbt Version**: Latest stable (e.g., `1.7`)
5. **Deployment Credentials**: Use the Snowflake connection configured earlier
6. Click **"Save"**

#### Production Environment

1. Go to **Environments** → **Create Environment**
2. **Name**: `Production`
3. **Environment Type**: Deployment
4. **dbt Version**: Latest stable (same as dev)
5. **Deployment Credentials**: Use the Snowflake connection configured earlier
6. **Custom Environment Variables** (optional):
   - `DBT_TARGET`: `prod`
7. Click **"Save"**

### 3.5 Set Up Environment Variables

In dbt Cloud, go to **Project Settings → Environment Variables** and add:

| Variable Name | Value | Environment | Secret |
|---------------|-------|-------------|--------|
| `SNOWFLAKE_ACCOUNT` | `<your_account>` | All | No |
| `SNOWFLAKE_USER` | `DBT_USER` | All | No |
| `SNOWFLAKE_PASSWORD` | `<password>` | All | Yes |
| `SNOWFLAKE_ROLE` | `DBT_ROLE` | All | No |
| `SNOWFLAKE_WAREHOUSE` | Your default warehouse | All | No |

### 3.6 Initialize the Project

1. Open the **dbt Cloud IDE**
2. In the command line, run:

```bash
# Install dependencies
dbt deps

# Compile models (verify no errors)
dbt compile

# Run staging models
dbt run --select staging

# Run all models
dbt run

# Run tests
dbt test
```

3. Verify all models build successfully

### 3.7 Create Production Job

1. Go to **Jobs** → **Create Job**
2. Configure the job:

   - **Job Name**: `pokemon_go_production`
   - **Environment**: Production
   - **dbt Version**: Latest stable
   - **Target Name**: `prod`
   - **Threads**: 4
   
   - **Commands**:
     ```
     dbt deps
     dbt run
     dbt test
     ```
   
   - **Schedule**: 
     - **Enabled**: Yes
     - **Frequency**: Daily at 2:00 AM (your timezone)
     - **Days**: Every day
     - Rationale: Runs after Fivetran sync (1 AM) + buffer
   
   - **Advanced Settings**:
     - **Generate docs on run**: Yes
     - **Run on source freshness**: No (not needed for this pipeline)

3. Click **"Save"**

### 3.8 Test Production Job

1. Click **"Run Now"** on the production job
2. Monitor the run in real-time
3. Verify all models build successfully
4. Check that tests pass

Expected results:
- ✅ 8 staging models built (views)
- ✅ 7 marts models built (tables)
- ✅ All tests pass

---

## 4. Orchestration Configuration

### 4.1 Get dbt Cloud API Credentials

1. In dbt Cloud, go to **Account Settings** (gear icon)
2. Navigate to **API Access**
3. Click **"Create Service Account Token"**
4. Configure:
   - **Token Name**: `Fivetran Webhook`
   - **Permissions**: 
     - ✅ Job Admin (to trigger jobs)
   - **Projects**: Select `pokemon_go_dbt`
5. Click **"Create"**
6. **Copy the token** (you won't see it again!)

### 4.2 Get dbt Cloud Job ID

1. In dbt Cloud, go to **Jobs**
2. Click on your `pokemon_go_production` job
3. Look at the URL: `https://cloud.getdbt.com/accounts/<ACCOUNT_ID>/projects/<PROJECT_ID>/jobs/<JOB_ID>`
4. Copy the `<JOB_ID>` (e.g., `12345`)

### 4.3 Configure Fivetran Webhook

1. In Fivetran, go to your Pokémon connector
2. Navigate to **Settings** → **Webhooks**
3. Click **"Add Webhook"**
4. Select **"dbt Cloud"** as the webhook type
5. Configure:

   - **dbt Cloud Account ID**: Your dbt Cloud account ID (from URL)
   - **dbt Cloud Job ID**: `<JOB_ID>` from step 4.2
   - **API Token**: The service account token from step 4.1
   - **Trigger Condition**: "After sync completes successfully"
   - **Cause**: "Fivetran sync completed"

6. Click **"Test Webhook"**
   - This will trigger a test run of your dbt job
   - Verify the test succeeds

7. Click **"Save"**

### 4.4 Verify Webhook Integration

1. In Fivetran, manually trigger a sync (or wait for the next scheduled sync)
2. After the sync completes, check dbt Cloud:
   - Go to **Jobs** → **Run History**
   - Verify a new run was triggered automatically
   - Check that the run was triggered by "Fivetran" (not manually)

Expected flow:
```
Fivetran Sync Starts (1:00 AM)
   ↓
Fivetran Sync Completes (1:30 AM)
   ↓
Fivetran Webhook Fires
   ↓
dbt Cloud Job Triggered (1:30 AM)
   ↓
dbt Transformations Complete (1:35 AM)
   ↓
Fresh data available in POKEMON_MARTS
```

---

## 5. Validation & Testing

### 5.1 End-to-End Pipeline Test

Run a complete end-to-end test:

1. **Trigger Fivetran Sync**:
   - In Fivetran, click **"Sync Now"**
   - Wait for sync to complete (~30 min)

2. **Verify dbt Job Triggered**:
   - Check dbt Cloud run history
   - Verify webhook triggered the job

3. **Verify Data in Snowflake**:

```sql
USE DATABASE jason_chletsos;

-- Check staging views
USE SCHEMA pokemon_staging;
SHOW VIEWS;
SELECT COUNT(*) FROM STG_POKEMON;

-- Check marts tables
USE SCHEMA pokemon_marts;
SHOW TABLES;

-- Verify data freshness
SELECT 
    'DIM_POKEMON' AS table_name,
    COUNT(*) AS row_count,
    MAX(_fivetran_synced) AS last_synced
FROM DIM_POKEMON
UNION ALL
SELECT 
    'FCT_POKEMON_STATS',
    COUNT(*),
    MAX(synced_at)
FROM FCT_POKEMON_STATS;

-- Test mart queries
SELECT * FROM MART_TOP_ATTACKERS LIMIT 10;
SELECT * FROM MART_TOP_DEFENDERS LIMIT 10;
SELECT * FROM MART_LEGENDARY_RANKINGS LIMIT 10;
```

### 5.2 Data Quality Checks

Run these queries to verify data quality:

```sql
-- Check for null primary keys
SELECT COUNT(*) AS null_pokemon_ids
FROM jason_chletsos.pokemon_marts.DIM_POKEMON
WHERE pokemon_id IS NULL;
-- Expected: 0

-- Check for duplicate pokemon
SELECT pokemon_id, COUNT(*) AS duplicate_count
FROM jason_chletsos.pokemon_marts.DIM_POKEMON
GROUP BY pokemon_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows

-- Verify tier classifications
SELECT tier, COUNT(*) AS pokemon_count
FROM jason_chletsos.pokemon_marts.MART_TOP_ATTACKERS
GROUP BY tier
ORDER BY tier;
-- Expected: S, A, B, C tiers with reasonable distributions

-- Check type effectiveness matrix completeness
SELECT COUNT(DISTINCT attacking_type) AS attacking_types,
       COUNT(DISTINCT defending_type) AS defending_types,
       COUNT(*) AS total_matchups
FROM jason_chletsos.pokemon_marts.MART_TYPE_EFFECTIVENESS;
-- Expected: ~18 attacking types, ~18 defending types, ~324 matchups
```

### 5.3 Performance Validation

Check query performance:

```sql
-- Enable query profiling
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- Test query performance (should be < 1 second)
SELECT * 
FROM jason_chletsos.pokemon_marts.MART_TOP_ATTACKERS
WHERE tier = 'S'
ORDER BY overall_rank;

-- Check table sizes
SELECT 
    table_schema,
    table_name,
    row_count,
    bytes / (1024 * 1024) AS size_mb
FROM jason_chletsos.INFORMATION_SCHEMA.TABLES
WHERE table_schema IN ('pokemon_staging', 'pokemon_marts')
ORDER BY bytes DESC;
```

---

## 6. Monitoring & Maintenance

### 6.1 Fivetran Monitoring

Monitor these metrics in the Fivetran dashboard:

- **Sync Status**: Should show "Succeeded" after each sync
- **Sync Duration**: Typically 30-60 minutes for initial sync, faster for incremental
- **Rows Synced**: Should be consistent (unless new Pokémon are added to PokéAPI)
- **API Errors**: Should be 0 (or very low)

Set up alerts:
1. Go to **Notifications** in Fivetran
2. Enable alerts for:
   - ❌ Sync failures
   - ⚠️ Sync delays (> 2 hours)
   - ⚠️ Schema changes detected

### 6.2 dbt Cloud Monitoring

Monitor these metrics in dbt Cloud:

- **Job Status**: Should show "Success" for all runs
- **Run Duration**: Typically 2-5 minutes
- **Test Failures**: Should be 0
- **Model Build Failures**: Should be 0

Set up alerts:
1. Go to **Job Settings** → **Notifications**
2. Enable email/Slack alerts for:
   - ❌ Job failures
   - ⚠️ Test failures
   - ⚠️ Long-running jobs (> 10 minutes)

### 6.3 Snowflake Monitoring

Monitor warehouse usage:

```sql
-- Check warehouse credit usage (last 7 days)
SELECT 
    DATE_TRUNC('day', start_time) AS date,
    warehouse_name,
    SUM(credits_used) AS total_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
    AND warehouse_name = '<YOUR_WAREHOUSE_NAME>'
GROUP BY date, warehouse_name
ORDER BY date DESC;

-- Check query performance
SELECT 
    query_text,
    execution_status,
    total_elapsed_time / 1000 AS seconds,
    rows_produced
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE warehouse_name = '<YOUR_WAREHOUSE_NAME>'
    AND start_time >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
ORDER BY total_elapsed_time DESC
LIMIT 10;
```

### 6.4 Maintenance Tasks

#### Weekly

- ✅ Review Fivetran sync logs for errors
- ✅ Review dbt Cloud job runs for failures
- ✅ Check data freshness in Snowflake

#### Monthly

- ✅ Review warehouse credit usage and optimize if needed
- ✅ Check for new PokéAPI features or endpoints
- ✅ Update dbt packages: `dbt deps --upgrade`
- ✅ Review and optimize slow queries

#### Quarterly

- ✅ Review and update tier thresholds in mart models
- ✅ Add new marts based on user feedback
- ✅ Audit Snowflake permissions and roles
- ✅ Review and optimize Fivetran sync frequency

### 6.5 Troubleshooting Common Issues

#### Issue: Fivetran sync fails with "Rate limit exceeded"

**Solution**:
- PokéAPI has rate limits (100 requests per minute)
- The connector includes delays and retry logic
- If this persists, increase `page_size` to reduce number of requests
- Or decrease sync frequency to daily

#### Issue: dbt job fails with "Schema does not exist"

**Solution**:
```sql
-- Verify schemas exist
USE DATABASE jason_chletsos;
SHOW SCHEMAS LIKE 'pokemon%';

-- If missing, create them
CREATE SCHEMA IF NOT EXISTS jason_chletsos.pokemon_staging;
CREATE SCHEMA IF NOT EXISTS jason_chletsos.pokemon_marts;

-- Grant permissions to dbt role
GRANT ALL ON SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;
```

#### Issue: Webhook not triggering dbt job

**Solution**:
1. Verify webhook is enabled in Fivetran
2. Check dbt Cloud API token is valid
3. Verify job ID is correct
4. Test webhook manually in Fivetran UI
5. Check dbt Cloud audit logs for webhook requests

#### Issue: Queries are slow

**Solution**:
```sql
-- Add clustering to large tables
ALTER TABLE jason_chletsos.pokemon_marts.MART_BEST_MOVESETS
CLUSTER BY (pokemon_id);

-- Or increase warehouse size (if using custom warehouse)
ALTER WAREHOUSE <YOUR_WAREHOUSE> SET WAREHOUSE_SIZE = 'SMALL';

-- Or enable result caching
ALTER SESSION SET USE_CACHED_RESULT = TRUE;
```

---

## Summary Checklist

Use this checklist to verify your deployment:

### Snowflake Setup
- ✅ Database `jason_chletsos` exists
- ✅ Schemas `pokemon_raw`, `pokemon_staging`, `pokemon_marts` created
- ✅ Default warehouse configured
- ✅ Fivetran and dbt roles have proper permissions
- ✅ Permissions granted correctly

### Fivetran Connector
- ✅ Custom connector uploaded and validated
- ✅ Snowflake destination configured
- ✅ Connection tested successfully
- ✅ Initial sync completed
- ✅ Data verified in `POKEMON_RAW` schema
- ✅ Sync frequency set to daily

### dbt Cloud Project
- ✅ Project created and connected to Snowflake
- ✅ Git repository connected
- ✅ Environment variables configured
- ✅ Dependencies installed (`dbt deps`)
- ✅ Models compiled and run successfully
- ✅ Tests passing
- ✅ Production job created and tested

### Orchestration
- ✅ dbt Cloud API token created
- ✅ Fivetran webhook configured
- ✅ Webhook tested successfully
- ✅ End-to-end pipeline tested
- ✅ Monitoring and alerts configured

---

## Next Steps

After successful deployment:

1. **Build Dashboards**: Connect Tableau, Looker, or Power BI to `POKEMON_MARTS` schema
2. **Add More Marts**: Create custom marts for specific battle strategies
3. **Expand Data Sources**: Add PvPoke data or Pokémon GO Gamemaster JSON
4. **Optimize Performance**: Add clustering, adjust warehouse size as needed
5. **Share with Team**: Document query patterns and create user guides

---

## Support & Resources

- **Fivetran Documentation**: https://fivetran.com/docs
- **dbt Documentation**: https://docs.getdbt.com
- **Snowflake Documentation**: https://docs.snowflake.com
- **PokéAPI Documentation**: https://pokeapi.co/docs/v2

For issues, check:
1. Fivetran connector logs
2. dbt Cloud run logs
3. Snowflake query history
4. This deployment guide's troubleshooting section

---

**Deployment Complete! 🎉**

Your Pokémon GO data pipeline is now live and running automatically.
