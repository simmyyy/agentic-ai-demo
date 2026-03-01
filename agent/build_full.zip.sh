#!/bin/bash
# Builds Lambda deployment package (Mac → Linux).
# Run: ./build_full.zip.sh [amd64|arm64]
# Default: amd64 (lambda_full_x86.zip)
# Ref: https://github.com/simmyyy/ie-microsoft-capstone/tree/main/bio_agent

set -e
cd "$(dirname "$0")"

ARCH="${1:-amd64}"

build_for() {
  local plat=$1
  local suffix=$2
  local BUILD_DIR="lambda_build_$suffix"
  rm -rf "$BUILD_DIR"
  mkdir -p "$BUILD_DIR"

  echo "=== Building for $plat (Mac → Linux) ==="
  echo "1. Copying code..."
  cp lambda_handler.py "$BUILD_DIR/"
  cp -r tools "$BUILD_DIR/"

  echo "2. Installing packages (Linux $plat)..."
  docker run --platform "$plat" --rm --entrypoint "" \
    -v "$(pwd)/$BUILD_DIR:/var/task" \
    -w /var/task \
    public.ecr.aws/lambda/python:3.12 \
    pip install requests boto3 -t . --no-cache-dir

  echo "3. Creating zip..."
  cd "$BUILD_DIR"
  zip -r ../lambda_full_$suffix.zip . -x "*.pyc" -x "__pycache__/*"
  cd ..
  echo "Done: lambda_full_$suffix.zip"
}

if [ "$ARCH" = "arm64" ]; then
  build_for "linux/arm64" "arm"
elif [ "$ARCH" = "amd64" ]; then
  build_for "linux/amd64" "x86"
else
  build_for "linux/amd64" "x86"
fi

echo ""
echo "Upload zip to Lambda:"
echo "  - Lambda x86_64 -> lambda_full_x86.zip"
echo "  - Lambda arm64  -> lambda_full_arm.zip"
echo ""
echo "Lambda environment variables:"
echo "  ALERT_TABLE_NAME=AlertAggregates (optional, default)"
echo "  AWS_REGION=us-east-2 (optional)"
echo "  ACCOUNT_SERVICE_URL, PAYMENTS_SERVICE_URL (for GetBankServicesHealth)"
