"""AWS Lambda entry point.

Mangum translates an API Gateway event into the ASGI calls that FastAPI
expects, so exactly the same application code runs locally under uvicorn and
in Lambda. Nothing in app/ needs to know where it is running.
"""

from mangum import Mangum

from app.main import app

# api_gateway_base_path strips the deployment stage (e.g. /prod) from the path
# before FastAPI sees it, so routes stay identical in both environments.
handler = Mangum(app, api_gateway_base_path="/prod", lifespan="off")
