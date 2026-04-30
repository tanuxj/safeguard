# Safeguard Flow Guide

This repo has two apps:

- `p1frontend`: React + Vite client
- `p1backend`: FastAPI + Tortoise backend

This README focuses on how data and requests flow through both layers.

## High-Level Architecture

1. User interacts with React pages (`/`, `/signup`, `/login`, `/dashboard`, `/send/public/:token`).
2. Frontend calls backend APIs through a shared Axios client.
3. Backend validates auth (JWT access token) for private routes.
4. Backend reads/writes PostgreSQL via Tortoise models (`users`, `sends`).
5. Backend returns JSON (or file bytes for file sends).
6. Frontend renders success/error states and next actions.

## Frontend Flow

### App startup and routing

- Entry point is `p1frontend/src/main.tsx`, which renders `App`.
- `p1frontend/src/App.tsx` defines routes:
  - `/` -> landing page
  - `/signup` -> register flow
  - `/login` -> login flow
  - `/dashboard` -> authenticated send management
  - `/send/public/:token` -> public share view
- On app mount, `bootstrapAuthSession()` tries to refresh access token if only refresh token exists.

### Auth token storage and refresh

- `authStorage.ts` strategy:
  - `access_token` in `sessionStorage` (tab/session scoped)
  - `refresh_token` in `localStorage` (persists across browser restarts)
- `api.ts` adds `Authorization: Bearer <access_token>` on each request.
- If an API call returns `401`, frontend automatically calls `POST /auth/refresh`, stores new access token, and retries once.
- If refresh fails, tokens are cleared and user must log in again.

### Signup/Login journey

- `Signup.tsx` posts to `POST /auth/register`.
- `Login.tsx` posts to `POST /auth/login`.
- On success:
  - save access + refresh tokens
  - navigate to `/dashboard`
- On failure:
  - show backend message in toast

### Dashboard journey

`Dashboard.tsx` is the main authenticated workspace.

- Initial load: calls `GET /send/mine` to list user sends.
- Create send:
  - Text send -> `POST /send/text` with JSON
  - File send -> `POST /send/file` with `multipart/form-data`
- Manage sends:
  - Open preview -> `GET /send/public-data/{share_token}`
  - Delete -> `DELETE /send/{send_id}`
  - Edit expiry -> `PATCH /send/{send_id}/deletion-date`
  - Copy link -> uses browser clipboard API

### Public share journey

`PublicSend.tsx` handles recipients opening shared links.

- Fetch metadata/content from `GET /send/public-data/{share_token}`.
- If password protected:
  - API returns `password required` until password is supplied.
  - Frontend re-calls endpoint with `?password=...`.
- For file sends, frontend downloads from:
  - `GET /send/public-file/{share_token}` (optional `password` query param).

## Backend Flow

### App setup

- `p1backend/main.py` creates FastAPI app.
- Routers included:
  - `app/auth/routes.py` (`/auth/*`)
  - `app/send/routes.py` (`/send/*`)
- Tortoise ORM is registered with PostgreSQL connection from `DATABASE_URL`.

### Auth flow (`/auth`)

- `POST /auth/register`
  - validates fields
  - checks if email exists
  - hashes password
  - creates user row
  - returns access + refresh tokens
- `POST /auth/login`
  - finds user by email
  - verifies password hash
  - returns access + refresh tokens
- `POST /auth/refresh`
  - validates refresh token
  - issues new access token

Token details:

- Access token expiry: 1 hour
- Refresh token expiry: 11 days
- Token type is tracked in payload (`type: access` / `type: refresh`)

### Send flow (`/send`)

- Private endpoints require Bearer access token via `get_access_payload_from_header()`.

Create:

- `POST /send/text`
  - validates timezone-aware deletion date
  - validates optional protection password
  - creates text send with unique `share_token`
- `POST /send/file`
  - validates file size (<= 50MB)
  - stores file in Cloudflare R2 if configured, else local `uploads/sends`
  - creates file send row with metadata

Read/manage:

- `GET /send/mine` -> list current user's sends
- `DELETE /send/{send_id}` -> owner delete
- `PATCH /send/{send_id}/deletion-date` -> owner update expiry

Public access:

- `GET /send/public/{share_token}` -> redirects to frontend route
- `GET /send/public-data/{share_token}`
  - checks existence, expiry, and view limit
  - enforces password if configured
  - increments `view_count` for non-owner access
  - returns send text/file metadata
- `GET /send/public-file/{share_token}`
  - same guards as public-data
  - returns binary file bytes with attachment headers

### Data model summary

- `users` table:
  - `id`, `first_name`, `last_name`, `email`, `password`, timestamps
- `sends` table:
  - owner (`user_id`)
  - content fields (`send_type`, `text_to_share`, file metadata)
  - controls (`deletion_date`, `password_hash`, `limit_views`, `view_count`)
  - sharing (`share_token`)

## End-to-End User Journeys

### 1) Register -> Login session

1. User submits signup/login form in frontend.
2. Backend validates and returns tokens.
3. Frontend stores tokens and routes to dashboard.
4. Future private API calls carry access token automatically.

### 2) Create a send

1. User fills send form on dashboard.
2. Frontend sends JSON (text) or multipart (file) payload.
3. Backend creates send, stores metadata/content, generates `share_token`.
4. Backend returns `share_link`.
5. Frontend shows link and refreshes "My Sends" list.

### 3) Recipient opens shared link

1. Recipient opens `/send/public/:token` in frontend.
2. Frontend requests public send data from backend.
3. Backend checks:
   - send exists
   - not expired
   - view limit not reached
   - correct password (if protected)
4. Frontend renders text OR offers file download.

## Environment Variables to Know

Frontend:

- `VITE_API_BASE_URL` -> backend base URL (for all API calls)

Backend core:

- `DATABASE_URL`
- `FRONTEND_BASE_URL` (for redirect endpoint)

Backend file storage (optional R2):

- `R2_ENDPOINT_URL`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_REGION` (optional, defaults to `auto`)
- `R2_PUBLIC_BASE_URL` (optional)

## Notes

- Backend currently returns JSON messages for many validation/auth failures instead of explicit HTTP error codes everywhere. Frontend handles this by checking `message` in responses.
- JWT secret is currently hardcoded in code and should be moved to environment variables for production.
