#!/bin/bash
# Attaches DynamoDB + App Runner permissions to the Lambda execution role.
# Run: ./setup-lambda-role.sh <LAMBDA_ROLE_NAME>
# Example: ./setup-lambda-role.sh bank-agent-lambda-role
# Find role name: Lambda → Configuration → Permissions → Execution role

set -e

ROLE_NAME="${1:?Usage: $0 <LAMBDA_ROLE_NAME>}"
POLICY_NAME="BankAgentLambdaPolicy"
REGION="${AWS_REGION:-us-east-2}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TABLE_ARN="arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/AlertAggregates"

echo "=== Attaching DynamoDB + App Runner policy to Lambda role ==="
echo "Role: $ROLE_NAME"
echo "Table: AlertAggregates ($REGION)"
echo ""

POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:GetItem",
        "dynamodb:BatchGetItem",
        "dynamodb:DescribeTable"
      ],
      "Resource": [
        "${TABLE_ARN}",
        "${TABLE_ARN}/index/*"
      ]
    },
    {
      "Sid": "AppRunnerAccess",
      "Effect": "Allow",
      "Action": [
        "apprunner:ListServices",
        "apprunner:DescribeService",
        "apprunner:ResumeService"
      ],
      "Resource": "*"
    }
  ]
}
EOF
)

aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document "$POLICY"

echo "Policy '$POLICY_NAME' attached to role '$ROLE_NAME'"
echo ""
echo "Lambda can now:"
echo "  - Query DynamoDB AlertAggregates (GetAlertSummary)"
echo "  - List App Runner services"
echo "  - Describe service status (RUNNING/PAUSED)"
echo "  - Resume paused services"
echo ""
