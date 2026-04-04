# How to use the Knowledge Base API

You have access to Nick's Knowledge Base API, which lets you search his Obsidian vault by semantic similarity and retrieve the full content of any matched file. The vault contains personal notes, project documentation, and research.

Base URL: `https://api.knowledge-base.dashanddata.com`

All requests require a Bearer token in the Authorization header. Your token:

```
cDcOfQg9CZLlcdI1lfOuGbo2pBiIFF741iqZS7OffAQ
```

The typical workflow is:

1. Search for relevant notes using the matches endpoint.
2. Read the `snippet` fields to decide which files are worth reading in full.
3. Retrieve the full content of specific files using the file endpoint.

---

## Search notes

### Description

Send a natural language question and receive the top 5 most relevant notes from the vault, ranked by cosine similarity. Each result includes the file name, path, a relevance score (0 to 1), and a short snippet of the file content.

Use this to find notes that are relevant to a topic the user is asking about.

### How to make a request

Make an HTTP POST request to `/obsidian/matches` with a JSON body containing a `question` field.

```
POST https://api.knowledge-base.dashanddata.com/obsidian/matches
Content-Type: application/json
Authorization: Bearer <token>

{
  "question": "What did Nick write about focus and deep work?"
}
```

### Expected response

Status 200. The response contains a `matches` array with up to 5 results, sorted by relevance:

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

If no notes match the query, the `matches` array will be empty. A 401 response means the token is missing or invalid.

---

## Retrieve a file

### Description

Fetch the full markdown content of a specific note by its UUID. Use the `id` value returned from the search endpoint.

Use this when a snippet from the search results looks relevant and you need the full text to answer the user's question.

### How to make a request

Make an HTTP GET request to `/obsidian/file/{file_id}` where `file_id` is the UUID from a search result.

```
GET https://api.knowledge-base.dashanddata.com/obsidian/file/a1b2c3d4-e5f6-7890-abcd-ef1234567890
Authorization: Bearer <token>
```

### Expected response

Status 200. The response contains the file metadata and full markdown content:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "deep-work.md",
  "file_path": "productivity/deep-work.md",
  "content": "# Deep Work\n\nDeep work is the ability to focus without distraction on a cognitively demanding task..."
}
```

A 404 response means the file UUID doesn't exist in the database or the file is no longer on disk. A 401 response means the token is missing or invalid.
