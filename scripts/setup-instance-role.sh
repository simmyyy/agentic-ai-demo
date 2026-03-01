#!/bin/bash
# Creates IAM Instance Role for App Runner with DynamoDB permissions.
# Run once, then assign the role in App Runner (Configuration → Security → Instance role).

set -e

ROLE_NAME="AppRunnerDynamoDBInstanceRole"
POLICY_NAME="AppRunnerDynamoDBPolicy"
REGION="${AWS_REGION:-us-east-2}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TABLE_ARN="arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/AlertAggregates"

echo "=== Creating App Runner Instance Role ==="
echo "Role: $ROLE_NAME"
echo "Table: AlertAggregates ($REGION)"
echo ""

# Trust policy – App Runner must be able to assume this role
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "tasks.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Policy – full permissions on AlertAggregates table
DYNAMODB_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DescribeTable",
        "dynamodb:ConditionCheckItem"
      ],
      "Resource": [
        "${TABLE_ARN}",
        "${TABLE_ARN}/index/*"
      ]
    }
  ]
}
EOF
)

# 1. Create role
echo ">>> Creating role $ROLE_NAME..."
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document "$TRUST_POLICY" \
  --description "Instance role for App Runner – DynamoDB AlertAggregates access" \
  2>/dev/null && echo "Role created" || {
  if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    echo "Role already exists (skipping)"
  else
    exit 1
  fi
}

# 2. Attach inline policy (or overwrite if exists)
echo ">>> Attaching DynamoDB policy..."
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document "$DYNAMODB_POLICY"
echo "Policy attached"

# 3. Show role ARN
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo ""
echo "=== Done ==="
echo ""
echo "Role ARN: $ROLE_ARN"
echo ""
echo "Next step:"
echo "  1. AWS Console → App Runner → account-service (or payments-service)"
echo "  2. Configuration → Edit"
echo "  3. Security → Instance role → select: $ROLE_NAME"
echo "  4. Save changes (triggers new deployment)"
echo ""
