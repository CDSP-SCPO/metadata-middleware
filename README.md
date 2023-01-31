# OAI middleware

Small python server that forwards requests to an OAI endpoint, make some changes to the response and forwards it back.

## How to use

### Development

Install the dependencies:

```sh
pip install -r requirements.txt
```

Start the dev server:

```sh
uvicorn main:app --reload
```

### Production

The Dockerfile can be used for production.

## Customisation

There are two environment variables (used in `main.py`):

- `OAI_ENDPOINT`: OAI endpoint to use
- `OAI_ENDPOINT_DEV`: secondary endpoint for testing

This middleware is currently used to fix metadata compatibility issues between <https://data.sciencespo.fr> and <https://entrepot.recherche.data.gouv.fr>. A mapping for the values (`MAPPINGS` variable in `main.py`) transforms source metadata values to make metadata compatible.

Each key of the `MAPPINGS` dictionary represent a path on the server. For instance:

```python
MAPPINGS = {
    "rdg": {
        "Audio": "Audiovisual",
        "Numeric": "Dataset",
        "StillImage": "Image",
    },
}
```

In this configuration, values will be changed from `Audio` to `Audiovisual` and so on under the `/rdg/oai` (and `/dev/rdg/oai` for the secondary endpoint) path.

### TLDR

- `/<mapping_name>/oai` will forward requests to the `OAI_ENDPOINT` and replace all the values in the response following the mapping at the `<mapping_name>` key.
- `/dev/<mapping_name>/oai` will forward requests to the `OAI_ENDPOINT_DEV` and replace all the values in the response following the mapping at the `<mapping_name>` key.

## Dataverse

This server can be used to be harvested by Dataverse instances. To do that, follow the usual harvesting client creation process ([official documentation](https://guides.dataverse.org/en/latest/admin/harvestclients.html)) using the `Server URL`. The `Archive URL` must be changed to the original Dataverse domain so dataset links do not use this middleware URL to build source URLs.

### Cannot find the `Archive URL` field?

The harvesting client must be saved a first time then edited again in order for the field to appear on the last page of the client settings.

## Possible improvements

- Allow different types of response modifications, not only mappings between values
- Create a path that forwards requests/responses without any modification (for testing or to have a single endpoint for all harvester clients). This could be achieved by creating an empty mapping.
- A way to customise the application without changing the code
- ...
