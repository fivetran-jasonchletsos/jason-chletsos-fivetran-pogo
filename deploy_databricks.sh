#!/usr/bin/env bash
# deploy_databricks.sh
# Packages the databricks_app/ directory, uploads to S3, and triggers CodeBuild.
# Usage: ./deploy_databricks.sh
set -euo pipefail

PROFILE="pokemon-app"
REGION="us-east-1"
BUCKET="pokemon-databricks-build-249080915751"
CODEBUILD_PROJECT="pokemon-databricks-deploy"
APP_DIR="databricks_app"

echo "==> Packaging ${APP_DIR}/ ..."
cd "$(dirname "$0")"

# Create a zip of the databricks_app contents (buildspec.yml must be at root of zip)
cd "${APP_DIR}"
zip -r ../databricks_source.zip . -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"
cd ..

echo "==> Uploading source.zip to s3://${BUCKET}/source.zip ..."
aws s3 cp databricks_source.zip "s3://${BUCKET}/source.zip" \
  --region "${REGION}" --profile "${PROFILE}"

rm -f databricks_source.zip

echo "==> Starting CodeBuild project: ${CODEBUILD_PROJECT} ..."
BUILD_ID=$(aws codebuild start-build \
  --project-name "${CODEBUILD_PROJECT}" \
  --region "${REGION}" --profile "${PROFILE}" \
  --query 'build.id' --output text)

echo "==> Build started: ${BUILD_ID}"
echo "==> Monitor at: https://console.aws.amazon.com/codesuite/codebuild/projects/${CODEBUILD_PROJECT}/build/${BUILD_ID}/log?region=${REGION}"
echo ""
echo "==> App will be available at: http://pokemon-databricks-alb-682300987.us-east-1.elb.amazonaws.com"
