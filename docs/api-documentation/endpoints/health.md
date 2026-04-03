# health

The health endpoint is defined directly on the main FastAPI app in `src/app.py`. It serves as a health check and index page.

## GET /

Returns an HTML page displaying the application name.

- no authentication required

### parameters

- none

### Sample Request

```bash
curl --location 'http://localhost:8007/'
```

### Sample Response

```html
<!doctype html>
<html>
<head><title>Knowledge Base Service</title></head>
<body><h1>Knowledge Base Service</h1></body>
</html>
```

- content-type is `text/html; charset=utf-8`
- status code is `200`
