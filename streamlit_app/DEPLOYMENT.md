# AWS App Runner Deployment Guide

Deploy the Streamlit app to a public HTTPS URL using AWS App Runner.
No servers, no load balancers, no SSL certs to manage.
Authentication uses AWS SSO (IAM Identity Center) — no long-lived access keys needed.

---

## Live deployment

| Resource | Value |
|---|---|
| **App URL** | https://spfimguasp.us-east-1.awsapprunner.com |
| Service ARN | `arn:aws:apprunner:us-east-1:249080915751:service/pokemon-go-analytics/8e8833b191704fbeac11614584235efa` |
| ECR image | `249080915751.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest` |
| Secret ARN | `arn:aws:secretsmanager:us-east-1:249080915751:secret:pokemon-app/snowflake-private-key-5POotd` |
| Instance role | `arn:aws:iam::249080915751:role/PokemonAppRunnerRole` |
| ECR access role | `arn:aws:iam::249080915751:role/PokemonAppRunnerECRRole` |

---

## AWS resources created

| Service | Resource name | Purpose |
|---|---|---|
| Secrets Manager | `pokemon-app/snowflake-private-key` | Snowflake RSA private key injected at runtime |
| ECR | `pokemon-go-analytics` | Docker image registry |
| IAM | `PokemonAppRunnerRole` | Instance role — lets the app read Secrets Manager |
| IAM | `PokemonAppRunnerECRRole` | Build role — lets App Runner pull from ECR |
| App Runner | `pokemon-go-analytics` | Hosts the Streamlit container |

---

## SSO login (required before any AWS CLI command)

SSO sessions expire after ~8 hours. Re-authenticate with:

```bash
aws sso login --profile pokemon-app
aws sts get-caller-identity --profile pokemon-app   # verify
```

---

## Updating the app after code changes

```bash
# 1. Re-login if needed
aws sso login --profile pokemon-app

# 2. Rebuild and push
cd /Users/jason.chletsos/Documents/GitHub/jason-chletsos-fivetran-pogo/streamlit_app

aws ecr get-login-password --region us-east-1 --profile pokemon-app \
  | docker login --username AWS --password-stdin \
    249080915751.dkr.ecr.us-east-1.amazonaws.com

docker buildx build --platform linux/amd64 -t pokemon-go-analytics:latest .

docker tag pokemon-go-analytics:latest \
  249080915751.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest

docker push 249080915751.dkr.ecr.us-east-1.amazonaws.com/pokemon-go-analytics:latest

# 3. Trigger redeployment
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-east-1:249080915751:service/pokemon-go-analytics/8e8833b191704fbeac11614584235efa \
  --region us-east-1 \
  --profile pokemon-app
```

---

## Local development (no Docker, no AWS needed)

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
