# Backend API - VectorShift Pipeline Builder

FastAPI backend for pipeline validation and processing....

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
# Development server with auto-reload
uvicorn main:app --reload

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /

Health check endpoint.

**Response:**

```json
{ "Ping": "Pong" }
```

### POST /pipelines/parse

Validate pipeline structure and detect cycles.

**Request:**
Form data with `pipeline` parameter containing JSON string.

**Response:**

```json
{
  "num_nodes": 5,
  "num_edges": 4,
  "is_dag": true
}
```

## DAG Detection Algorithm

Uses Depth-First Search (DFS) with recursion stack tracking:

1. Build adjacency list from edges
2. Perform DFS traversal from each unvisited node
3. Detect cycles by checking if node is in recursion stack

Time Complexity: O(V + E) where V = vertices, E = edges
Space Complexity: O(V) for visited and recursion stack

## Dependencies

- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- python-multipart==0.0.6
- pydantic==2.5.0

## CORS Configuration

Configured to allow requests from `http://localhost:3000` (React dev server).
