# obsidian

The obsidian router is defined in `src/routes/obsidian.py`. All endpoints in this router require Bearer token authentication.

## POST /obsidian/matches

Accepts a natural language question, converts it to an embedding, and returns the top 5 most similar markdown files from the vault using pgvector cosine similarity search.

- authentication required (Bearer token)

### parameters

- `question` (string, required) — the natural language query to search against stored embeddings

### Sample Request

```bash
curl --location 'http://localhost:8007/obsidian/matches' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <token>' \
--data '{"question": "What did I write about focus and deep work?"}'
```

### Sample Response

```json
{
  "matches": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "file_name": "deep-work.md",
      "file_path": "productivity/deep-work.md",
      "score": 0.9412,
      "snippet": "First 500 characters of the file..."
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "file_name": "focus-strategies.md",
      "file_path": "notes/focus-strategies.md",
      "score": 0.8734,
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

#### Missing question field (422)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

## GET /obsidian/file/{file_id}

Retrieves the full markdown content of a file by its UUID. Looks up the record in the `markdown_files` table and reads the file from disk.

- authentication required (Bearer token)

### parameters

- `file_id` (UUID, path, required) — the UUID of the markdown file record

### Sample Request

```bash
curl --location 'http://localhost:8007/obsidian/file/a1b2c3d4-e5f6-7890-abcd-ef1234567890' \
--header 'Authorization: Bearer <token>'
```

### Sample Response

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "deep-work.md",
  "file_path": "productivity/deep-work.md",
  "content": "# Deep Work\n\nDeep work is the ability to focus without distraction..."
}
```

### Error responses

#### Missing or invalid token (401)

```json
{
  "detail": "Invalid or missing API key"
}
```

#### File not found in database or on disk (404)

```json
{
  "detail": "File not found"
}
```

#### Invalid UUID format (422)

```json
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": ["path", "file_id"],
      "msg": "Input should be a valid UUID",
      "input": "not-a-uuid"
    }
  ]
}
```
