# FastAPI + PostgreSQL + Docker Setup

This project uses:

* FastAPI
* PostgreSQL
* Docker + Docker Compose
* Tortoise ORM
* Aerich (for migrations)
* uv (Python package manager)

---

# Project Setup

## Start Project

Build and start containers:

```bash
docker compose up --build
```

This will:

* start PostgreSQL
* start FastAPI backend
* run database migrations automatically using `aerich upgrade`

---

# Stop Project

## Stop containers

```bash
docker compose down
```

## Stop containers + remove volumes

```bash
docker compose down -v
```

Use `-v` only when you want a fresh database.

---

# Database Access

## Connect to PostgreSQL container

```bash
docker exec -it p1_db psql -U tanuj -d postgres
```

## Useful PostgreSQL commands

Show tables:

```sql
\dt
```

Expanded display:

```sql
\x
```

Check users data:

```sql
SELECT * FROM users;
```

Exit:

```sql
\q
```

---

# Aerich Migrations

## First-time initialization

Run only once:

```bash
docker exec -it p1_backend uv run aerich init-db
```

This creates:

* migrations folder
* initial migration
* database schema

---

## Create new migration after model changes

```bash
docker exec -it p1_backend uv run aerich migrate --name update_users
```

Example:

```bash
docker exec -it p1_backend uv run aerich migrate --name create_users_table
```

---

## Apply migrations

```bash
docker exec -it p1_backend uv run aerich upgrade
```

---

# Important Difference

## `migrate` vs `upgrade`

### migrate

Creates migration files.

Use when:

* model code changes

### upgrade

Applies migration files to database.

Use when:

* starting project
* deploying changes

---

# Manual Backend Commands

## Enter backend container

```bash
docker exec -it p1_backend sh
```

## Run uv sync manually

```bash
uv sync
```

Usually this is already handled in Dockerfile.

---

# Auto Migration on Startup

We use `entrypoint.sh`:

```sh
#!/bin/sh

sleep 5

uv run aerich upgrade

uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

This ensures migrations run automatically when Docker starts.

---

# Common Fixes

## Role does not exist

Example:

```text
FATAL: role "tanuj" does not exist
```

Fix:

```bash
docker compose down -v
docker compose up --build
```

This recreates database with correct `.env` values.

---

## Aerich command not found

Wrong:

```bash
aerich migrate
```

Correct:

```bash
uv run aerich migrate
```

Because Aerich is installed inside project virtual environment.

---

## PowerShell remove venv issue

Wrong:

```powershell
rmdir /s /q .venv
```

Correct:

```powershell
Remove-Item -Recurse -Force .venv
```

---

# Environment Variables Example

```env
DATABASE_URL=postgres://tanuj:dev@db:5432/postgres
POSTGRES_USER=tanuj
POSTGRES_PASSWORD=dev
POSTGRES_DB=postgres
```

---

# File Uploads in Production (Cloudflare R2)

File Sends support S3-compatible storage through Cloudflare R2.

In production, configure R2 so uploaded files are stored in cloud object storage instead of local container disk.

## Required R2 environment variables

```env
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<your-access-key-id>
R2_SECRET_ACCESS_KEY=<your-secret-access-key>
R2_BUCKET_NAME=<your-bucket-name>
```

## Optional R2 environment variables

```env
R2_REGION=auto
R2_PUBLIC_BASE_URL=https://files.example.com
```

Notes:

* `R2_REGION` defaults to `auto` (recommended for Cloudflare R2).
* `R2_PUBLIC_BASE_URL` is optional and not required for current backend download flow.
* Never commit secrets to Git.

## How upload/download works

* Upload API: `POST /send/file`
* Files are stored in R2 with user/date-based keys and a unique filename suffix to avoid overwrite collisions.
* Download API: `GET /send/public-file/{share_token}`
* Backend fetches bytes from R2 and streams the file to the client.

## Deployment checklist

* Add all R2 env vars to your server/container runtime.
* Restart backend after env update.
* Test by uploading a file, then opening the generated share link and downloading it.
* Verify object appears in your R2 bucket.

## Fallback behavior

If R2 configuration is missing or temporarily unavailable, backend falls back to local storage under `uploads/sends`.

For production, keep R2 env vars configured correctly so uploads do not rely on local container filesystem.

---

# Current Main Tables

* users
  n- aerich

---

# Development Flow

## Normal work

```bash
docker compose up --build
```

## After model changes

```bash
docker exec -it p1_backend uv run aerich migrate --name update_users

docker exec -it p1_backend uv run aerich upgrade
```

## Fresh database reset

```bash
docker compose down -v

docker compose up --build
```

---

# Notes

* UUID is preferred for production IDs
* Passwords should always be hashed
* Never store plain text passwords
* Use `.env` for DB credentials
* Keep migrations version controlled
