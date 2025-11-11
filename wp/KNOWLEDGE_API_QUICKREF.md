# Knowledge API Quick Reference

## Base URL
```
/api/knowledge
```

## Authentication
```http
X-API-Key: your_api_key
```

## Endpoints

### 1. List Entries
```http
GET /api/knowledge/entries
```
**Parameters:** `page`, `page_size`, `search`, `status`, `tag`, `date_from`, `date_to`, `sort`, `order`

**Example:**
```bash
curl -H "X-API-Key: key" \
  "http://localhost:5000/api/knowledge/entries?status=completed&page_size=20"
```

---

### 2. Get Tags
```http
GET /api/knowledge/tags
```
**Returns:** `{ tags: [], count: N }`

**Example:**
```bash
curl -H "X-API-Key: key" \
  "http://localhost:5000/api/knowledge/tags"
```

---

### 3. Get Status Counts
```http
GET /api/knowledge/statuses
```
**Returns:** `{ statuses: {...}, total: N }`

**Example:**
```bash
curl -H "X-API-Key: key" \
  "http://localhost:5000/api/knowledge/statuses"
```

---

### 4. Export CSV
```http
GET /api/knowledge/export
```
**Parameters:** `fields` (comma-separated), all filters from list endpoint

**Example:**
```bash
curl -H "X-API-Key: key" \
  "http://localhost:5000/api/knowledge/export?fields=article_title,status" \
  -o export.csv
```

---

### 5. Get Entry Detail
```http
GET /api/knowledge/entry/{article_id}
```

**Example:**
```bash
curl -H "X-API-Key: key" \
  "http://localhost:5000/api/knowledge/entry/abc123"
```

---

## Common Filters

| Filter | Values | Example |
|--------|--------|---------|
| `status` | pending, processing, transferred, completed, failed | `?status=completed` |
| `sort` | created_at, updated_at, title, status | `?sort=title` |
| `order` | ASC, DESC | `?order=ASC` |
| `date_from` | YYYY-MM-DD | `?date_from=2024-01-01` |
| `date_to` | YYYY-MM-DD | `?date_to=2024-12-31` |
| `search` | any string | `?search=关键词` |
| `tag` | tag name | `?tag=category` |

## Response Format

### Success
```json
{
  "success": true,
  "data": { ... },
  "summary": { ... }
}
```

### Error
```json
{
  "success": false,
  "error": "Error code",
  "message": "详细说明"
}
```

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (missing/invalid API key) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Export Fields

Available fields for CSV export:
- `article_id`
- `article_title`
- `article_url`
- `original_link`
- `original_password`
- `new_link`
- `new_password`
- `new_title`
- `status`
- `error_message`
- `tag`
- `created_at`
- `updated_at`

## Python Quick Start

```python
import requests

headers = {'X-API-Key': 'your_key'}
base_url = 'http://localhost:5000'

# Get entries
response = requests.get(
    f'{base_url}/api/knowledge/entries',
    headers=headers,
    params={'status': 'completed', 'page_size': 10}
)
data = response.json()

# Export CSV
response = requests.get(
    f'{base_url}/api/knowledge/export',
    headers=headers,
    params={'fields': 'article_title,status'}
)
with open('export.csv', 'wb') as f:
    f.write(response.content)
```

## JavaScript Quick Start

```javascript
const headers = { 'X-API-Key': 'your_key' };
const baseUrl = 'http://localhost:5000';

// Get entries
fetch(`${baseUrl}/api/knowledge/entries?status=completed`, { headers })
  .then(res => res.json())
  .then(data => console.log(data));

// Export CSV
fetch(`${baseUrl}/api/knowledge/export?fields=article_title,status`, { headers })
  .then(res => res.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'export.csv';
    a.click();
  });
```

## UI Routes

- `GET /kb` - Knowledge base UI homepage
- `GET /kb/{path}` - UI assets (CSS, JS, images)

## Testing

```bash
# Run smoke tests
cd /home/engine/project/wp
python3 smoke_test_knowledge_api.py

# Run interactive examples
python3 example_knowledge_api.py
```

## Documentation

- Full API docs: `README_KNOWLEDGE_API.md`
- Implementation details: `KNOWLEDGE_API_IMPLEMENTATION.md`
- Repository layer: `README_KNOWLEDGE_REPO.md`
- Swagger UI: http://localhost:5000/docs
