from os import getenv

from fastapi import FastAPI, HTTPException, Request, Response
from httpx import AsyncClient

# Initialize FastAPI and disable the documentation
app = FastAPI(docs_url=None, redoc_url=None)

# Initialize the asynchronous client
client = AsyncClient()

# Settings
OAI_ENDPOINT = getenv("OAI_ENDPOINT", "https://data.sciencespo.fr/oai")
OAI_ENDPOINT_DEV = getenv("OAI_ENDPOINT_DEV", "https://datapprd.sciencespo.fr/oai")

# Mappings
KINDOFDATA_MAPPING_RDG = {
    "Audio": "Audiovisual",
    "Numeric": "Dataset",
    "StillImage": "Still image",
}


async def replace_content(content: str, mapping: dict) -> str:
    """Replace the content of a string using a dictionary"""

    for old_value, new_value in mapping.items():
        content = content.replace(old_value, new_value)
    return content


async def handle_oai_response(request: Request, oai_endpoint: str) -> Response:
    """Handle the OAI response"""

    # Get the query to forward from the request
    query = request.url.query
    if not query:
        return HTTPException(status_code=400, detail="No query specified")

    # Build the source path
    source_path = f"{oai_endpoint}?{query}"

    r = await client.get(source_path)
    # If the status is not OK, use the same status code as the source and its reason phrase
    if r.status_code != 200:
        return HTTPException(status_code=r.status_code, detail=r.reason_phrase)

    # Replace the content of the response
    content = await replace_content(r.text, KINDOFDATA_MAPPING_RDG)

    return Response(
        headers={
            # Cache for an hour
            # "Cache-Control": "max-age=3600",
            # Alternative location of the content (keep a link to the source)
            "Content-Location": source_path,
        },
        media_type="application/xml",
        content=content,
    )


@app.get("/dev/oai")
async def oai_dev(request: Request) -> Response:
    return await handle_oai_response(request, OAI_ENDPOINT_DEV)


@app.get("/oai")
async def oai(request: Request) -> Response:
    return await handle_oai_response(request, OAI_ENDPOINT)
