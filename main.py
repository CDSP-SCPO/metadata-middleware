from os import getenv

from fastapi import FastAPI, HTTPException, Request, Response
from httpx import AsyncClient
from uvicorn import run as run_uvicorn

# Settings
OAI_ENDPOINT = getenv("OAI_ENDPOINT", "https://data.sciencespo.fr/oai")
OAI_ENDPOINT_DEV = getenv("OAI_ENDPOINT_DEV", "https://datapprd.sciencespo.fr/oai")

# We must change the endpoint in the response because of the pagination
ENDPOINT_MAPPING = {
    OAI_ENDPOINT: "https://export-data.sciencespo.fr/oai",
    OAI_ENDPOINT_DEV: "https://export-dataverse-pprd.cdsp.sciences-po.fr/oai",
}

# Mapping keys are used in the routes. Example: "/<key>/oai"
MAPPINGS = {
    "rdg": {
        "<dc:type>Audio</dc:type>": "<dc:type>Audiovisual</dc:type>",
        "<dc:type>Numeric</dc:type>": "<dc:type>Dataset</dc:type>",
        "<dc:type>StillImage</dc:type>": "<dc:type>Image</dc:type>",
        "<dc:type>Video</dc:type>": "<dc:type>Audiovisual</dc:type>",
    },
}

# Initialize FastAPI and disable the documentation
app = FastAPI(docs_url=None, redoc_url=None)

# Initialize the asynchronous client
client = AsyncClient()


async def replace_content(content: str, mapping: dict) -> str:
    """Replace the content of a string using a dictionary"""

    for old_value, new_value in mapping.items():
        content = content.replace(old_value, new_value)
    return content


async def handle_oai_response(
    request: Request, oai_endpoint: str, mapping: dict
) -> Response:
    """Handle the OAI response"""

    if not mapping:
        raise HTTPException(status_code=404)

    # Get the query to forward from the request
    query = request.url.query
    if not query:
        raise HTTPException(status_code=400, detail="No query specified")

    # Build the source path
    source_path = f"{oai_endpoint}?{query}"

    r = await client.get(source_path)
    # If the status is not OK, use the same status code as the source and its reason phrase
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.reason_phrase)

    # Replace the content of the response
    content = await replace_content(r.text, mapping)

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


@app.get("/dev/{mapping}/oai")
async def oai_dev(mapping: str, request: Request) -> Response:
    return await handle_oai_response(
        request,
        OAI_ENDPOINT_DEV,
        {
            OAI_ENDPOINT_DEV: ENDPOINT_MAPPING.get(OAI_ENDPOINT_DEV),
            **MAPPINGS.get(mapping),
        },
    )


@app.get("/{mapping}/oai")
async def oai(mapping: str, request: Request) -> Response:
    return await handle_oai_response(
        request,
        OAI_ENDPOINT,
        {
            OAI_ENDPOINT: ENDPOINT_MAPPING.get(OAI_ENDPOINT),
            **MAPPINGS.get(mapping),
        },
    )


if __name__ == "__main__":
    run_uvicorn(app, host="0.0.0.0", port=8000, reload=True)
