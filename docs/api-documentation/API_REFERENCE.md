# Knowledge Base Service API Reference

This API is a FastAPI Python service that provides endpoints for querying semantic embeddings of an Obsidian vault stored in PostgreSQL with pgvector.

This file serves as the top-level API index.

Each resource has its own documentation under the [`/endpoints`](./endpoints) folder:

- [health](./endpoints/health.md)
- [obsidian](./endpoints/obsidian.md)

File names should be in lower case and follow the pattern of their router subdomain. This means routers that have two words will have a hyphen between them. If we make a router for the subdomain "contract-users-teams" the file will be named docs/api-documentation/endpoints/contract-users-teams.md.

## Authentication

All `/obsidian/*` endpoints require a Bearer token in the `Authorization` header. Tokens are generated via the `scripts/generate_token.py` CLI and validated by hashing with SHA-256 and comparing against the `api_keys` table.

## Endpoint documentation format

Each file should be a router file.
Include an example of the reqeust in curl and the response in json.

Minimize the user of bold text. Never use it in section headings or the beginning of a listed item.

Each endpoint should have its own section with a heading that follows the pattern of the endpoint.

## [METHOD] /[router-file-name]/[endpoint]

[description]

- include if authentication is required

### parameters

- list in bullet format

### Sample Request

```bash
curl --location 'http://localhost:8007/obsidian/matches' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <token>' \
--data '{"question": "What did I write about focus?"}'
```

### Sample Response

```json
{
  "matches": [
    {
      "id": "a1b2c3d4-...",
      "file_name": "deep-work.md",
      "file_path": "productivity/deep-work.md",
      "score": 0.94,
      "snippet": "First 500 characters of the file..."
    }
  ]
}
```

### Error responses

#### Missing or invalid token (401)

```json
{
  "detail": "Invalid or missing API key"
}
```

### [Optional section for additional information]

- This section should be used sparingly
