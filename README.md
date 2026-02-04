# Travel Planner API

A Django REST API for managing travel projects and their places, using the Art Institute of Chicago API as the external source for places.

A “place” is an artwork from the **Art Institute of Chicago API**, so you can only add an `external_id` if it actually exists there.

## Tech stack

- Python / Django
- Django REST Framework (DRF)
- drf-spectacular (OpenAPI/Swagger docs)
- PostgreSQL (via Docker) or SQLite (default)
- Docker & docker-compose (optional but supported)

## Setup (without Docker)

1. Clone the repo and enter the directory:

   ```bash
   git clone <YOUR_REPO_URL>
   cd travel-planner
   ```

2. Create and activate a virtualenv (example with `venv`):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root (example):

   ```env
   DJANGO_SECRET_KEY=your-secret-key
   DJANGO_DEBUG=true
   DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

   POSTGRES_DB=travel_planner
   POSTGRES_USER=travel_planner
   POSTGRES_PASSWORD=changeme-postgres-password
   DB_HOST=localhost
   DB_PORT=5432
   ```

   - If `POSTGRES_DB` is not set, the app will use SQLite (`db.sqlite3`) automatically.

5. Run migrations and start the server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

6. Open in browser:

   - Swagger UI: `http://127.0.0.1:8000/api/docs/`
   - OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## Setup with Docker (PostgreSQL)


1. Ensure your `.env` has PostgreSQL variables set.
2. Build and start containers:

   ```
   docker compose up --build
   ```

3. Access:

   - Swagger UI: `http://localhost:8000/api/docs/`
   - API root: `http://localhost:8000/api/projects/`

## API Overview

### Projects

- **Create project (optionally with places)**  
  `POST /api/projects/`

  **Body example:**

  ```json
  {
    "name": "Paris Trip",
    "description": "Museums and galleries",
    "start_date": "2026-05-01",
    "places_input": [
      { "external_id": 27992, "notes": "Must see" },
      { "external_id": 129884, "notes": "If time allows" }
    ]
  }
  ```

  **Rules:**

  - Max 10 places per project.
  - No duplicate `external_id` within the same project.
  - Each `external_id` must exist in the Art Institute of Chicago API, otherwise the request fails.

- **List projects**  
  `GET /api/projects/`

  Optional query params:

  - `?is_completed=true|false`
  - `?name=<substring>`

- **Retrieve project**  
  `GET /api/projects/{project_id}/`

- **Update project**  
  `PATCH /api/projects/{project_id}/`  
  (only `name`, `description`, `start_date` — `is_completed` is computed)

- **Delete project (with guard)**  
  `DELETE /api/projects/{project_id}/`

  - Fails if any place in the project has `visited = true`.

### Project Places

- **List places for a project**  
  `GET /api/projects/{project_id}/places/`

  Optional: `?visited=true|false`

- **Add place to a project**  
  `POST /api/projects/{project_id}/places/`

  **Body:**

  ```json
  {
    "external_id": 27992,
    "notes": "Night visit"
  }
  ```

  **Rules:**

  - Max 10 places per project (including existing ones).
  - Cannot add the same `external_id` to the same project more than once.
  - Place must exist in the Art Institute API.

- **Get single place**  
  `GET /api/projects/{project_id}/places/{place_id}/`

- **Update place (notes / visited)**  
  `PATCH /api/projects/{project_id}/places/{place_id}/`

  **Body example:**

  ```json
  {
    "visited": true,
    "notes": "Visited on day 2"
  }
  ```

  When all places in a project are `visited = true`, the project’s `is_completed` becomes `true`.

## Documentation / Postman

- OpenAPI schema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`
