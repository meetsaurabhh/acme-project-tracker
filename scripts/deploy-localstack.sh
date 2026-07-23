#!/usr/bin/env bash
# Mac / Linux equivalent of deploy-localstack.ps1
set -euo pipefail
cd "$(dirname "$0")/.."

INFRA_DIR="infra/localstack"
BUILD_DIR="$INFRA_DIR/build"

echo "==> 1/6 Checking LocalStack is awake"
curl -sf http://localhost:4566/_localstack/health > /dev/null || {
  echo "LocalStack is not answering on port 4566."
  echo "Start it with:  docker compose --profile cloud up -d"
  exit 1
}

echo "==> 2/6 Packaging the Lambda"
rm -rf "$BUILD_DIR" && mkdir -p "$BUILD_DIR"
docker run --rm \
  -v "$PWD/backend:/src:ro" \
  -v "$PWD/$BUILD_DIR:/out" \
  python:3.12-slim \
  bash -c "pip install --quiet --target /out/package -r /src/requirements-lambda.txt && cp -r /src/app /out/package/ && cp /src/lambda_handler.py /out/package/ && find /out/package -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; true"

echo "==> 3/6 Zipping"
(cd "$BUILD_DIR/package" && zip -qr ../lambda.zip .)

echo "==> 4/6 Provisioning infrastructure with Terraform"
pushd "$INFRA_DIR" > /dev/null
terraform init -input=false > /dev/null
terraform apply -auto-approve
API_URL=$(terraform output -raw api_url)
BUCKET=$(terraform output -raw site_bucket)
SITE_URL=$(terraform output -raw website_url)
popd > /dev/null

echo "==> 5/6 Building the frontend against $API_URL"
pushd frontend > /dev/null
echo "VITE_API_URL=$API_URL" > .env.production
[ -d node_modules ] || npm install
npm run build
popd > /dev/null

echo "==> 6/6 Uploading the build to S3"
docker run --rm --network acme-net \
  -v "$PWD/frontend/dist:/dist:ro" \
  -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test -e AWS_DEFAULT_REGION=ap-south-1 \
  amazon/aws-cli \
  s3 sync /dist "s3://$BUCKET" --delete --endpoint-url http://localstack:4566

echo
echo "Deployed."
echo "  Website  $SITE_URL"
echo "  API      $API_URL/health"
