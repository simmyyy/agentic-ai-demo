#!/bin/bash
# Creates AlertState and Incidents DynamoDB tables.
# Run once. Tables use pk (String) and sk (String) as keys.

set -e

REGION="${AWS_REGION:-us-east-2}"

echo "=== Creating DynamoDB tables ==="
echo "Region: $REGION"
echo ""

# AlertState: snapshot, context, actions
aws dynamodb create-table \
  --table-name AlertState \
  --attribute-definitions \
    AttributeName=pk,AttributeType=S \
    AttributeName=sk,AttributeType=S \
  --key-schema \
    AttributeName=pk,KeyType=HASH \
    AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" \
  2>/dev/null && echo "AlertState created" || echo "AlertState exists or error"

# Incidents
aws dynamodb create-table \
  --table-name Incidents \
  --attribute-definitions \
    AttributeName=pk,AttributeType=S \
    AttributeName=sk,AttributeType=S \
  --key-schema \
    AttributeName=pk,KeyType=HASH \
    AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" \
  2>/dev/null && echo "Incidents created" || echo "Incidents exists or error"

echo ""
echo "=== Done ==="
