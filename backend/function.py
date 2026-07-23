"""AWS Lambda entry point for the ACME Project Tracker service.

The workshop platform invokes `handler(event, context)` in this file. Mangum
translates the API Gateway event into the ASGI calls FastAPI expects, so the
same application code runs under uvicorn locally and as a Lambda in the cloud.
"""

import os

from mangum import Mangum

from app.main import app

# API Gateway serves this function under /api/<service-name>. Stripping that
# base path means FastAPI sees the same routes it does in local development.
_BASE_PATH = os.getenv("API_GATEWAY_BASE_PATH", "")

# lifespan is disabled because Lambda has no long-running startup phase.
handler = Mangum(app, api_gateway_base_path=_BASE_PATH or None, lifespan="off")
