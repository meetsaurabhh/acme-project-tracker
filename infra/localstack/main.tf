# Deploys the ACME Project Tracker to LocalStack: an AWS emulator running in
# Docker on this machine. The resource definitions are real AWS resources --
# only the endpoints differ from a live account.
#
# Architecture on the free Hobby tier:
#   S3            static website hosting the React build
#   Lambda        the FastAPI backend, wrapped by Mangum
#   API Gateway   public HTTP entry point that forwards everything to Lambda
#   PostgreSQL    stays in Docker, because RDS needs a paid LocalStack plan

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "acme-project-tracker"
}

variable "database_url" {
  description = "How the Lambda reaches PostgreSQL. 'db' is the Docker service name."
  type        = string
  default     = "postgresql+psycopg2://acme:acme@db:5432/acme_pm"
}

variable "jwt_secret" {
  type      = string
  default   = "localstack-dev-secret"
  sensitive = true
}

# Credentials are ignored by LocalStack but the provider insists on them.
provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3             = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    apigateway     = "http://localhost:4566"
    iam            = "http://localhost:4566"
    sts            = "http://localhost:4566"
    cloudformation = "http://localhost:4566"
    cloudwatchlogs = "http://localhost:4566"
  }
}

# --------------------------------------------------------------- frontend: S3
resource "aws_s3_bucket" "site" {
  bucket        = "${var.project_name}-site"
  force_destroy = true
}

resource "aws_s3_bucket_website_configuration" "site" {
  bucket = aws_s3_bucket.site.id

  index_document { suffix = "index.html" }

  # Single-page app: unknown paths must still load index.html so React Router
  # can handle them, otherwise a refresh on /projects/3 returns a 404.
  error_document { key = "index.html" }
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadForWebsite"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.site.arn}/*"
    }]
  })
}

# ------------------------------------------------------------- backend: Lambda
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_lambda_function" "api" {
  function_name    = "${var.project_name}-api"
  role             = aws_iam_role.lambda.arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 512
  filename         = "${path.module}/build/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/build/lambda.zip")

  environment {
    variables = {
      DATABASE_URL = var.database_url
      JWT_SECRET   = var.jwt_secret
      CORS_ORIGINS = "*"
    }
  }
}

# ------------------------------------------------------ API Gateway REST API
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.project_name}-api"
  description = "Forwards every request to the FastAPI Lambda."
}

# {proxy+} catches every path; ANY catches every HTTP method. FastAPI does the
# real routing, so API Gateway does not need to know about individual endpoints.
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# The root path (/) is a separate resource from {proxy+} and needs its own wiring.
resource "aws_api_gateway_method" "root" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_rest_api.api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_rest_api.api.root_resource_id
  http_method             = aws_api_gateway_method.root.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_deployment" "api" {
  depends_on = [
    aws_api_gateway_integration.proxy,
    aws_api_gateway_integration.root,
  ]
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeploy = sha1(jsonencode([
      aws_api_gateway_resource.proxy.id,
      aws_api_gateway_integration.proxy.id,
      aws_lambda_function.api.source_code_hash,
    ]))
  }

  lifecycle { create_before_destroy = true }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.api.id
  stage_name    = "prod"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

# ---------------------------------------------------------------- outputs
output "site_bucket" {
  value = aws_s3_bucket.site.id
}

output "website_url" {
  description = "Open this in a browser once the frontend has been uploaded."
  value       = "http://${aws_s3_bucket.site.id}.s3-website.localhost.localstack.cloud:4566"
}

output "api_url" {
  description = "Base URL of the deployed API."
  value       = "http://localhost:4566/restapis/${aws_api_gateway_rest_api.api.id}/prod/_user_request_"
}

output "lambda_name" {
  value = aws_lambda_function.api.function_name
}
