#!/bin/bash
# Build and push both services to ECR, then trigger deployment in App Runner.
# Requires: ECR repositories agentic-demo/account-service, agentic-demo/payments-service
#            (create in AWS Console → ECR → Create repository)

set -e

REGION=${AWS_REGION:-$(aws configure get region)}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

ACCOUNT_URI="${REGISTRY}/agentic-demo/account-service"
PAYMENTS_URI="${REGISTRY}/agentic-demo/payments-service"

echo "=== Region: $REGION, Account: $ACCOUNT_ID ==="
echo "Account:  $ACCOUNT_URI"
echo "Payments: $PAYMENTS_URI"
echo ""

# Create ECR repositories if they don't exist
for repo in agentic-demo/account-service agentic-demo/payments-service; do
  aws ecr describe-repositories --repository-names "$repo" --region "$REGION" 2>/dev/null || \
  aws ecr create-repository --repository-name "$repo" --region "$REGION"
done

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"

# Region us-east-2 for DynamoDB (no credentials – App Runner uses Instance Role)
BUILD_ARGS=(--build-arg "AWS_REGION=us-east-2")

# Build and push account-service (linux/amd64 for App Runner – Mac M1/M2 builds arm64 by default)
echo ""
echo ">>> Build account-service..."
docker build --platform linux/amd64 "${BUILD_ARGS[@]}" -t "$ACCOUNT_URI:latest" ./services/account
echo ">>> Push account-service..."
docker push "$ACCOUNT_URI:latest"

# Build and push payments-service
echo ""
echo ">>> Build payments-service..."
docker build --platform linux/amd64 "${BUILD_ARGS[@]}" -t "$PAYMENTS_URI:latest" ./services/payments
echo ">>> Push payments-service..."
docker push "$PAYMENTS_URI:latest"

# Trigger deployment in App Runner (if services exist)
echo ""
echo ">>> Triggering App Runner deployment..."
ACCOUNT_ARN=$(aws apprunner list-services --region "$REGION" \
  --query "ServiceSummaryList[?ServiceName=='account-service'].ServiceArn" --output text 2>/dev/null || true)
PAYMENTS_ARN=$(aws apprunner list-services --region "$REGION" \
  --query "ServiceSummaryList[?ServiceName=='payments-service'].ServiceArn" --output text 2>/dev/null || true)

if [[ -n "$ACCOUNT_ARN" ]]; then
  aws apprunner start-deployment --service-arn "$ACCOUNT_ARN" --region "$REGION"
  echo "Account-service: deployment started"
else
  echo "Account-service: not found in App Runner (skipping)"
fi
if [[ -n "$PAYMENTS_ARN" ]]; then
  aws apprunner start-deployment --service-arn "$PAYMENTS_ARN" --region "$REGION"
  echo "Payments-service: deployment started"
else
  echo "Payments-service: not found in App Runner (skipping)"
fi

echo ""
echo "=== Done ==="
