# AWS App Runner Deployment Guide

Deploy the Streamlit app to a public HTTPS URL using AWS App Runner.
No servers, no load balancers, no SSL certs to manage.

---

## Prerequisites

- AWS CLI installed (`aws --version`)
- Docker Desktop installed — https://www.docker.com/products/docker-desktop/
- An AWS account with permissions to use: ECR, App Runner, Secrets Manager, IAM

---

## Step 1 — Configure AWS CLI

```bash
aws configure
```

Enter when prompted:
| Prompt | Value |
|---|---|
| AWS Access Key ID | *(from AWS Console → IAM → Your user → Security credentials → Create access key)* |
| AWS Secret Access Key | *(same page)* |
| Default region name | `us-east-1` |
| Default output format | `json` |

Verify it worked:
```bash
aws sts get-caller-identity
```
You should see your account ID and user ARN.

---

## Step 2 — Install Docker Desktop

1. Download from https://www.docker.com/products/docker-desktop/
2. Install and launch it
3. Verify: `docker --version`

---

## Step 3 — Store the Snowflake private key in AWS Secrets Manager

App Runner can't read files from your laptop. The private key is stored as a secret and
injected as an environment variable at runtime.

```bash
# Read your key file and store it as a secret (single command)
aws secretsmanager create-secret \
  --name "pokemon-app/snowflake-private-key" \
  --description "Snowflake RSA private key for Pokémon GO Analytics app" \
  --secret-string "$(cat /Users/jason.chletsos/rsa_key.p8)" \
  --region us-east-1
```

Note the `ARN` in the output — you'll need it in Step 7.

> The app reads this secret as the `SNOWFLAKE_PRIVATE_KEY_CONTENT` environment variable.
> The passphrase is hardcoded in `app.py` for local dev but is NOT needed in AWS because
> we strip the encryption when loading the key (the DER bytes are passed directly to the connector).
> If you want to store the passphrase as a secret too, repeat this step for it.

---

## Step 4 — Create an ECR repository

ECR (Elastic Container Registry) is where your Docker image lives.

```bash
aws ecr create-repository \
  --repository-name pokemon-go-analytics \
  --region us-east-1
```

Note the `repositoryUri` in the output. It looks like:
`123456789012.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics`

---

## Step 5 — Build and push the Docker image

```bash
cd /Users/jason.chletsos/Documents/GitHub/jason-chletsos-fivetran-pogo/streamlit_app

# Log Docker into ECR (replace ACCOUNT_ID with your 12-digit AWS account ID)
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin \
    ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build the image (Apple Silicon Mac — must target linux/amd64 for AWS)
docker buildx build --platform linux/amd64 \
  -t pokemon-go-analytics:latest .

# Tag it for ECR
docker tag pokemon-go-analytics:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest

# Push it
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest
```

---

## Step 6 — Create the App Runner IAM role

App Runner needs permission to pull from ECR and read from Secrets Manager.

```bash
# Create the trust policy file
cat > /tmp/apprunner-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "tasks.apprunner.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name PokemonAppRunnerRole \
  --assume-role-policy-document file:///tmp/apprunner-trust.json

# Attach Secrets Manager read access
aws iam attach-role-policy \
  --role-name PokemonAppRunnerRole \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

# Note the role ARN in the output — needed in Step 7
```

---

## Step 7 — Create the App Runner service

```bash
# Replace the three placeholders before running:
#   ACCOUNT_ID     — your 12-digit AWS account ID
#   SECRET_ARN     — the ARN from Step 3
#   ROLE_ARN       — the ARN from Step 6

aws apprunner create-service \
  --service-name pokemon-go-analytics \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8080",
        "RuntimeEnvironmentVariables": {
          "SNOWFLAKE_ACCOUNT":   "A3209653506471-SALES_ENG_DEMO",
          "SNOWFLAKE_USER":      "JASON.CHLETSOS@FIVETRAN.COM",
          "SNOWFLAKE_ROLE":      "SALES_DEMO_ROLE",
          "SNOWFLAKE_WAREHOUSE": "DEFAULT",
          "SNOWFLAKE_DATABASE":  "jason_chletsos"
        },
        "RuntimeEnvironmentSecrets": {
          "SNOWFLAKE_PRIVATE_KEY_CONTENT": "SECRET_ARN"
        }
      }
    },
    "AutoDeploymentsEnabled": false
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB",
    "InstanceRoleArn": "ROLE_ARN"
  }' \
  --region us-east-1
```

App Runner will provision the service. This takes ~3 minutes.

---

## Step 8 — Get your public URL

```bash
aws apprunner describe-service \
  --service-arn $(aws apprunner list-services --region us-east-1 \
    --query "ServiceSummaryList[?ServiceName=='pokemon-go-analytics'].ServiceArn" \
    --output text) \
  --region us-east-1 \
  --query "Service.ServiceUrl" \
  --output text
```

You'll get a URL like: `https://abc123xyz.us-east-1.awsapprunner.com`

Open it in a browser — the app is live.

---

## Updating the app after code changes

```bash
cd /Users/jason.chletsos/Documents/GitHub/jason-chletsos-fivetran-pogo/streamlit_app

# Rebuild and push
docker buildx build --platform linux/amd64 -t pokemon-go-analytics:latest .
docker tag pokemon-go-analytics:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest

# Trigger a new deployment
aws apprunner start-deployment \
  --service-arn YOUR_SERVICE_ARN \
  --region us-east-1
```

---

## Local development (no Docker needed)

```bash
cd /Users/jason.chletsos/Documents/GitHub/jason-chletsos-fivetran-pogo/streamlit_app

pip install -r requirements.txt
streamlit run app.py
# Opens at http://localhost:8501
```

---

## Cost estimate

| Service | Usage | Approx. monthly cost |
|---|---|---|
| App Runner | 1 vCPU / 2 GB, ~5 hrs/day active | ~$5–10 |
| ECR | 1 image (~500 MB) | ~$0.05 |
| Secrets Manager | 1 secret | ~$0.40 |
| **Total** | | **~$6–11/month** |

App Runner pauses compute when there's no traffic, so light usage is very cheap.
