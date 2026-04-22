from firebase_functions import https_fn, options
from starlette.testclient import TestClient
from fastapi import FastAPI
import logging
import traceback
from typing import Optional, Union

# Configure logging
logger = logging.getLogger("firebase_handler")
logger.setLevel(logging.INFO)

# Initialize FastAPI app
app = FastAPI()
client = TestClient(app)

@https_fn.on_request()
def Maike_Agent_With_Web_Search(req: https_fn.Request) -> https_fn.Response:
    """
    Firebase HTTP function that forwards the request to a FastAPI app using Starlette's TestClient.
    
    Args:
        req (https_fn.Request): The HTTP request object from Firebase Functions.
    
    Returns:
        https_fn.Response: The response from the FastAPI application.
    """
    try:
        logger.info(f"Received {req.method} request to {req.path}")

        # Set up FastAPI test client

        # Prepare full URL
        path = req.path
        query = req.query_string.decode("utf-8") if hasattr(req, "query_string") and req.query_string else ""
        full_url = f"{path}?{query}" if query else path

        # Prepare request content
        headers = dict(req.headers)
        body: Optional[Union[bytes, str]] = None
        if req.method in ("POST", "PUT", "PATCH"):
            body = req.get_data()

        # Forward request to FastAPI
        logger.debug(f"Forwarding {req.method} to {full_url}")
        response = client.request(
            method=req.method,
            url=full_url,
            headers=headers,
            content=body
        )

        logger.info(f"FastAPI responded with status {response.status_code}")

        return https_fn.Response(
            response=response.content,
            status=response.status_code,
            headers=dict(response.headers),
        )

    except Exception as e:
        logger.error(f"Error in firebase_handler: {e}")
        logger.error(traceback.format_exc())

        return https_fn.Response(
            response=f"Internal server error: {e}",
            status=500,
            headers={"Content-Type": "text/plain"},
        )
