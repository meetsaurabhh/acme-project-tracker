# Deploys the whole application to LocalStack.
#
#   .\scripts\deploy-localstack.ps1
#
# Prerequisites: Docker running, Terraform installed, LocalStack started with
#   docker compose --profile cloud up -d

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$InfraDir = "infra/localstack"
$BuildDir = "$InfraDir/build"

Write-Host "==> 1/6 Checking LocalStack is awake" -ForegroundColor Cyan
try {
    Invoke-RestMethod -Uri "http://localhost:4566/_localstack/health" -TimeoutSec 5 | Out-Null
} catch {
    Write-Host "LocalStack is not answering on port 4566." -ForegroundColor Red
    Write-Host "Start it with:  docker compose --profile cloud up -d"
    exit 1
}

Write-Host "==> 2/6 Packaging the Lambda (this uses Docker for Linux-compatible wheels)" -ForegroundColor Cyan
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path $BuildDir | Out-Null

# Install dependencies and copy source inside a Linux container, then zip it.
# Building on Windows directly would produce Windows binaries that Lambda cannot load.
docker run --rm `
    -v "${PWD}/backend:/src:ro" `
    -v "${PWD}/$BuildDir:/out" `
    python:3.12-slim `
    bash -c "pip install --quiet --target /out/package -r /src/requirements-lambda.txt && cp -r /src/app /out/package/ && cp /src/lambda_handler.py /out/package/ && cd /out/package && find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; true"

Write-Host "==> 3/6 Zipping" -ForegroundColor Cyan
Compress-Archive -Path "$BuildDir/package/*" -DestinationPath "$BuildDir/lambda.zip" -Force
$SizeMb = [math]::Round((Get-Item "$BuildDir/lambda.zip").Length / 1MB, 1)
Write-Host "    lambda.zip is $SizeMb MB"

Write-Host "==> 4/6 Provisioning infrastructure with Terraform" -ForegroundColor Cyan
Push-Location $InfraDir
terraform init -input=false | Out-Null
terraform apply -auto-approve
$ApiUrl = terraform output -raw api_url
$Bucket = terraform output -raw site_bucket
$SiteUrl = terraform output -raw website_url
Pop-Location

Write-Host "==> 5/6 Building the frontend against $ApiUrl" -ForegroundColor Cyan
Push-Location frontend
"VITE_API_URL=$ApiUrl" | Out-File -FilePath ".env.production" -Encoding ascii
if (-not (Test-Path "node_modules")) { npm install }
npm run build
Pop-Location

Write-Host "==> 6/6 Uploading the build to S3" -ForegroundColor Cyan
docker run --rm --network acme-net `
    -v "${PWD}/frontend/dist:/dist:ro" `
    -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test -e AWS_DEFAULT_REGION=ap-south-1 `
    amazon/aws-cli `
    s3 sync /dist "s3://$Bucket" --delete --endpoint-url http://localstack:4566

Write-Host ""
Write-Host "Deployed." -ForegroundColor Green
Write-Host "  Website  $SiteUrl"
Write-Host "  API      $ApiUrl/health"
Write-Host ""
Write-Host "The database is still the Docker 'db' container, because RDS needs a paid"
Write-Host "LocalStack plan. Everything else is running as real Lambda and S3."
