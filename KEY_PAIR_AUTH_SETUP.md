# Key Pair Authentication Setup Guide

This guide explains how to configure key pair authentication for the Pokémon GO dbt project.

## Prerequisites

✅ Your Snowflake administrator has already generated RSA key pairs for all users  
✅ Public keys are registered in Snowflake  
✅ You have access to your private key file  

## What You Need

1. **Private Key File Location**
   - Example: `~/.ssh/snowflake_key.p8` or `C:\Users\YourName\.ssh\snowflake_key.p8`
   - This file should have been provided by your Snowflake admin

2. **Private Key Passphrase** (if applicable)
   - If your private key is encrypted, you'll need the passphrase
   - Store this securely in a password manager

3. **Snowflake Username**
   - Your Snowflake username that has the public key registered

## Verify Your Key Pair is Configured

Run this in Snowflake to confirm your public key is registered:

```sql
DESC USER <YOUR_USERNAME>;
```

Look for `RSA_PUBLIC_KEY_FP` in the output. If present, your key pair is configured.

---

## Configuration Steps

### For dbt Cloud

1. **Navigate to Connection Settings**
   - Go to Project Settings → Connection
   - Select Snowflake as your data warehouse

2. **Configure Authentication**
   - **Username**: Your Snowflake username
   - **Authentication Method**: Select **"Key Pair"**
   - **Private Key**: Upload your private key file (e.g., `snowflake_key.p8`)
   - **Private Key Passphrase**: Enter your passphrase (leave blank if unencrypted)

3. **Set Environment Variables** (if using profiles.yml)
   - `SNOWFLAKE_ACCOUNT` = Your account identifier (e.g., `abc12345.us-east-1`)
   - `SNOWFLAKE_USER` = Your username
   - `SNOWFLAKE_ROLE` = Your role (e.g., `DBT_ROLE`)
   - `SNOWFLAKE_WAREHOUSE` = Your warehouse name
   - `SNOWFLAKE_PRIVATE_KEY_PATH` = Path to private key file
   - `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` = Your passphrase (mark as secret)

4. **Test Connection**
   - Click "Test Connection" to verify
   - Should see "Connection successful"

### For dbt Core (Local Development)

1. **Set Environment Variables**

```bash
# Linux/Mac
export SNOWFLAKE_ACCOUNT=abc12345.us-east-1
export SNOWFLAKE_USER=your_username
export SNOWFLAKE_ROLE=DBT_ROLE
export SNOWFLAKE_WAREHOUSE=YOUR_WAREHOUSE_NAME
export SNOWFLAKE_PRIVATE_KEY_PATH=~/.ssh/snowflake_key.p8
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase  # Optional if unencrypted
```

```powershell
# Windows PowerShell
$env:SNOWFLAKE_ACCOUNT="abc12345.us-east-1"
$env:SNOWFLAKE_USER="your_username"
$env:SNOWFLAKE_ROLE="DBT_ROLE"
$env:SNOWFLAKE_WAREHOUSE="YOUR_WAREHOUSE_NAME"
$env:SNOWFLAKE_PRIVATE_KEY_PATH="C:\Users\YourName\.ssh\snowflake_key.p8"
$env:SNOWFLAKE_PRIVATE_KEY_PASSPHRASE="your_passphrase"  # Optional if unencrypted
```

2. **Test Connection**

```bash
cd dbt_pokemon_go
dbt debug
```

You should see:
```
Connection test: [OK connection ok]
```

---

## Troubleshooting

### Error: "Private key file not found"

**Solution**: Verify the path to your private key file
```bash
# Linux/Mac
ls -la ~/.ssh/snowflake_key.p8

# Windows
dir C:\Users\YourName\.ssh\snowflake_key.p8
```

### Error: "JWT token invalid"

**Causes:**
- Public key not registered in Snowflake
- Wrong private key file
- Private key doesn't match public key

**Solution**: Contact your Snowflake admin to verify your public key registration

### Error: "Incorrect passphrase"

**Solution**: 
- Verify you're using the correct passphrase
- Try leaving passphrase blank if key is unencrypted
- Contact admin if you've lost the passphrase

### Error: "Permission denied"

**Solution**: Set correct file permissions
```bash
# Linux/Mac
chmod 600 ~/.ssh/snowflake_key.p8
```

---

## Security Best Practices

✅ **Never commit private keys to Git**
- Add `*.p8`, `*.pem` to `.gitignore`

✅ **Store passphrases securely**
- Use a password manager (1Password, LastPass, etc.)
- Never hardcode in scripts

✅ **Restrict file permissions**
- Private key should only be readable by you (`chmod 600`)

✅ **Use environment variables**
- Don't hardcode credentials in configuration files
- Use dbt Cloud's secret management for sensitive values

✅ **Rotate keys periodically**
- Follow your organization's key rotation policy
- Work with Snowflake admin to update keys

---

## Quick Reference

### dbt Cloud Environment Variables

| Variable | Example Value | Secret? |
|----------|---------------|---------|
| `SNOWFLAKE_ACCOUNT` | `abc12345.us-east-1` | No |
| `SNOWFLAKE_USER` | `jason.chletsos` | No |
| `SNOWFLAKE_ROLE` | `DBT_ROLE` | No |
| `SNOWFLAKE_WAREHOUSE` | `COMPUTE_WH` | No |
| `SNOWFLAKE_PRIVATE_KEY_PATH` | `~/.ssh/snowflake_key.p8` | No |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | `your_passphrase` | **Yes** |

### File Locations

| OS | Typical Private Key Location |
|----|------------------------------|
| Linux/Mac | `~/.ssh/snowflake_key.p8` |
| Windows | `C:\Users\YourName\.ssh\snowflake_key.p8` |

---

## Need Help?

- **Snowflake Admin**: For key pair generation/registration issues
- **dbt Documentation**: https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup#key-pair-authentication
- **Project Issues**: Check the main README.md troubleshooting section
