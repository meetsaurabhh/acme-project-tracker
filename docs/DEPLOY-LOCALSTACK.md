# Deploying to the cloud environment (LocalStack)

LocalStack is an AWS emulator. It runs in Docker on your own machine and
answers the same API calls the real AWS does, so you use real Terraform, real
`aws s3 sync`, and real Lambda packaging — but nothing leaves your laptop and
nothing is billed.

---

## What gets deployed

```
Browser
   │
   ├──► S3 static website ──────────── the React build
   │
   └──► API Gateway ──► Lambda ─────── the FastAPI backend (via Mangum)
                          │
                          └──► PostgreSQL in Docker
```

**Why PostgreSQL stays in Docker.** LocalStack's free Hobby tier covers S3,
Lambda, API Gateway REST API, IAM, CloudFormation and CloudWatch Logs. RDS and
CloudFront are Base-plan features. Rather than fake it, the database stays as
the Docker container you already have, and the Lambda connects to it over the
Docker network. Say that plainly if you are asked — knowing the boundary of
your own architecture is a better answer than pretending there isn't one.

The Terraform in `infra/terraform/main.tf` is the *real AWS* version, with RDS
and CloudFront. `infra/localstack/main.tf` is the one that runs here. Having
both is worth showing.

---

## Before you start

### 1. A LocalStack account

Since March 2026, even the free tier needs an auth token.

1. Sign up at https://app.localstack.cloud/sign-up
2. Go to your workspace → **Auth Token** → copy it.
3. In the project root, create a file called `.env` containing:

   ```
   LOCALSTACK_AUTH_TOKEN=ls-your-token-here
   ```

   `.gitignore` already excludes `.env`, so the token will not end up on GitHub.

> **Check with your workshop organisers first.** The Hobby plan's terms are for
> non-commercial use. If the workshop counts as commercial, they may have a
> licence for you to use instead.

### 2. Terraform

Download from https://developer.hashicorp.com/terraform/downloads, unzip it,
and put `terraform.exe` somewhere on your PATH (`C:\Windows\System32` works, or
create `C:\terraform` and add it to your PATH via System Environment
Variables).

Check it:

```powershell
terraform --version
```

---

## Deploying

### Step 1 — start LocalStack alongside your app

```powershell
docker compose --profile cloud up -d
```

The `--profile cloud` flag is what brings LocalStack in. Without it you get the
normal three containers and nothing else.

Confirm it is alive:

```powershell
curl http://localhost:4566/_localstack/health
```

You should get JSON listing the available services.

### Step 2 — run the deployment

```powershell
.\scripts\deploy-localstack.ps1
```

It does six things: checks LocalStack, packages the Lambda inside a Linux
container, zips it, runs `terraform apply`, rebuilds the frontend pointed at
the deployed API URL, and uploads the build to S3.

Expect three to five minutes on the first run.

### Step 3 — open what you deployed

The script prints two URLs at the end:

```
Website  http://acme-project-tracker-site.s3-website.localhost.localstack.cloud:4566
API      http://localhost:4566/restapis/<id>/prod/_user_request_/health
```

Open the website URL and sign in as usual. You are now using a React app served
from S3, talking to a FastAPI backend running as a Lambda function behind API
Gateway.

---

## Proving it actually deployed

Worth doing before a demo, because "it looks the same" is a fair challenge.

**List the S3 bucket contents:**

```powershell
docker run --rm --network acme-net -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test -e AWS_DEFAULT_REGION=ap-south-1 amazon/aws-cli s3 ls s3://acme-project-tracker-site --endpoint-url http://localstack:4566
```

**List the Lambda functions:**

```powershell
docker run --rm --network acme-net -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test -e AWS_DEFAULT_REGION=ap-south-1 amazon/aws-cli lambda list-functions --endpoint-url http://localstack:4566
```

**Watch the Lambda run:**

```powershell
docker compose logs -f localstack
```

Then click around the deployed site. You will see LocalStack spinning up a
container per invocation. That is the clearest possible demonstration that the
backend really is serverless now.

**The LocalStack web dashboard** at https://app.localstack.cloud/ shows your
local resources visually once you are signed in — an easy thing to put on a
screen during a presentation.

---

## Redeploying after a change

Same command. Terraform works out what changed and only updates that.

```powershell
.\scripts\deploy-localstack.ps1
```

## Tearing it down

```powershell
cd infra/localstack
terraform destroy -auto-approve
cd ../..
docker compose --profile cloud down
```

LocalStack forgets everything when it stops, so a fresh `up` gives you an empty
account. That is a feature, not a bug — it means your Terraform has to actually
work from scratch, every time.

---

## When something breaks

| Symptom | Cause | Fix |
|---|---|---|
| `LocalStack is not answering on port 4566` | Not started, or still booting | `docker compose --profile cloud up -d`, wait 30s |
| Terraform: `connection refused` | Same as above | As above |
| Lambda returns 502 | Packaging problem | `docker compose logs localstack` and look for the Python traceback |
| Lambda: `could not translate host name "db"` | Lambda not on the app network | Confirm `LAMBDA_DOCKER_NETWORK: acme-net` is in `docker-compose.yml`, then restart LocalStack |
| Website loads but every request fails | Frontend built against the wrong API URL | Rerun the deploy script; it regenerates `.env.production` |
| `terraform: command not found` | Not on PATH | Reopen the terminal after editing PATH |

The single most useful command when stuck:

```powershell
docker compose logs -f localstack
```

---

## What to say about this in your demo

Three points that show you understood rather than copied:

1. **The same application code runs in both places.** `lambda_handler.py` is
   four lines — Mangum translates API Gateway events into the ASGI protocol
   FastAPI already speaks. Nothing in `app/` knows or cares whether it is
   running under uvicorn or Lambda.

2. **The API Gateway config is deliberately dumb.** One `{proxy+}` resource and
   one `ANY` method forward everything to the Lambda, and FastAPI does the
   routing. The alternative — declaring all twenty-odd endpoints in Terraform —
   means changing infrastructure every time you add a route.

3. **The infrastructure is described, not clicked.** `terraform destroy`
   followed by `terraform apply` rebuilds the entire environment from the file.
   That is the actual point of infrastructure as code, and it is easy to
   demonstrate live.
