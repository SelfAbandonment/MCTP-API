# Community announcements and player management

All endpoints use the existing `{code, message, data}` JSON envelope. Errors use
the HTTP status as `code`; validation errors contain field errors in `data`.
All dates are timezone-aware ISO 8601 strings (UTC by default).

## Endpoints

| Method | Path (under `/api/v1/`) | Access / result |
| --- | --- | --- |
| GET | `announcements/` | Public, published and `published_at <= now` only; `?search=` |
| GET | `announcements/<id>/` | Public single announcement; 404 for drafts, scheduled and unknown ids |
| GET | `overview/` | Any authenticated user, counter snapshot |
| GET, POST | `manage/announcements/` | Active staff, list (`?search=`) / create |
| GET, PATCH, DELETE | `manage/announcements/<id>/` | Active staff, retrieve / update / delete |
| GET | `manage/players/?search=&page=` | Active staff, list / search |
| GET, PATCH | `manage/players/<id>/` | Active staff, retrieve / toggle active |

Lists return `data: {results: [...], count, next, previous}` with 20 records per
page. `next` / `previous` are absolute URL strings or null. The query parameter
is `page`, starting at 1; nonexistent pages return 404. Public announcements are
ordered by publication date then ID descending; management announcements by
creation date then ID descending; players by ID ascending.

The public list and the public detail endpoint share one visibility rule: a
record is public when `is_published` is true and `published_at <= now`. Drafts,
scheduled records and unknown ids therefore all return the same 404 from
`announcements/<id>/`, so the endpoint cannot be used to probe unpublished
content. Both endpoints are unauthenticated and ignore any `Authorization`
header, so a stale token never turns a public read into a 401.

`?search=` on `announcements/` uses DRF `SearchFilter` semantics over `title`,
`summary` and `body`. It only ever searches the public subset, so drafts and
scheduled records never leak through a keyword hit.

Public announcement objects contain `id, title, summary, body, published_at,
updated_at`. Management objects additionally contain `is_published, created_at`.
Creation requires nonblank `title` (max 160) and `body`. `summary` is optional
(blank default, max 240); `is_published` defaults false; `published_at` is nullable.
If a published announcement has no publication timestamp, create/update assigns
the current time. Explicit future timestamps schedule visibility. Unpublishing
does not erase an existing timestamp unless null is explicitly supplied.
PATCH changes only supplied fields. Unknown/read-only inputs return 400.
Body is plain text: clients must display it as text, never unsanitized HTML.
DELETE returns HTTP 200 with `{code:200,message:"success",data:null}`.

Player objects contain `id, username, email, is_active, is_staff, is_superuser,
date_joined, last_login, minecraft`. `minecraft` is null or `{uuid, username}`;
Microsoft IDs and refresh tokens are never returned. The binding is read from the
allauth `SocialAccount` first (current flow, `extra_data.mc_uuid` /
`mc_username`) and falls back to the legacy `MicrosoftAccount` row, matching the
`/api/v1/auth/me/` semantics. Case-insensitive search runs over username, email,
allauth `uid` (Minecraft UUID), allauth `extra_data.mc_username`, and the legacy
Minecraft username / UUID, so both binding generations are findable, with DRF
SearchFilter semantics for multiple terms. The list prefetches social accounts,
so rendering a page does not issue one query per row. PATCH accepts only
`{"is_active": true|false}`; empty, unknown and read-only fields return 400.
Self, staff (including inactive staff) and superuser accounts return 403 on
PATCH, even for a no-op. No user deletion or role changes are supported.
Disabled users cannot authenticate using existing access tokens.

`GET /api/v1/auth/me/` now also returns read-only `is_staff, is_superuser,
is_active` booleans. Existing `PUT /api/v1/auth/me/` remains partial and only
writes `username, email`; other fields are ignored, never persisted.
Password changes remain `POST /api/v1/auth/password/` with `old_password,
new_password, new_password_confirm`.

## Community overview

`GET /api/v1/overview/` requires authentication and returns counters only:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "announcements": { "published": 3, "latest_published_at": "2026-10-30T07:00:00Z" },
    "players": { "total": 12, "active": 11, "minecraft_bound": 7 },
    "generated_at": "2026-10-30T07:12:36.482913Z"
  }
}
```

`announcements.published` counts the same public subset as `announcements/`;
`latest_published_at` is null when that subset is empty. `players.total` includes
inactive accounts, `players.active` counts `is_active=True`, and
`players.minecraft_bound` counts distinct users with either a current allauth
Microsoft social account or a legacy `MicrosoftAccount` row, so a user holding
both is counted once. No usernames, emails, Microsoft IDs or tokens are exposed.
The endpoint performs four aggregate queries and does not paginate.

## Deployment and validation

Apply the new `community` migration during the normal release process.
No environment changes or external service dependencies are required.
Management authorization is checked server-side using active staff status,
not frontend role visibility; no new authentication mechanism is introduced.
OpenAPI schemas are available at `/api/schema/` and `/api/docs/`.

```powershell
uv run ruff check .
uv run ruff format --check mctp_api\community mctp_api\auth\serializers.py mctp_api\auth\views.py mctp_api\settings.py mctp_api\urls.py
uv run python manage.py check
uv run python manage.py test --verbosity=1
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py spectacular --validate --file community-schema.validation.yaml
```

Remove the generated validation schema after inspection. Django's test runner
uses its standard isolated test database; do not run `migrate` against the
existing development database just to test this feature.

## Isolated local end-to-end server

The production settings do **not** expose a database-path environment variable.
Do not assume `DATABASE_URL` or `DB_NAME` overrides SQLite. For local E2E only,
create a settings module in your session artifact folder (not in the repository)
with the following content, replacing the database path with a new artifact
SQLite file. Never point it at the existing repository database:

```python
from mctp_api.settings import *

DEBUG = True
SECRET_KEY = "isolated-local-e2e-only-not-for-deployment"
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
CORS_ALLOW_ALL_ORIGINS = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": r"C:\absolute\session\artifacts\community-e2e.sqlite3",
    }
}
MS_CLIENT_ID = ""
MS_CLIENT_SECRET = ""
MS_TOKEN_FERNET_KEY = ""
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
```

For example, save as `community_e2e_settings.py` and prepend its containing
folder to `PYTHONPATH`. From the backend repository:

```powershell
$env:PYTHONPATH = "C:\absolute\session\artifacts"
$env:DJANGO_SETTINGS_MODULE = "community_e2e_settings"
$env:DEBUG = "true"
$env:SECRET_KEY = "isolated-local-e2e-only-not-for-deployment"
uv run python manage.py migrate --noinput
# Load only explicitly approved fixtures into this new isolated database.
uv run python manage.py runserver 127.0.0.1:8000 --noreload
```

`DJANGO_SETTINGS_MODULE` and `PYTHONPATH` select the local override module.
Host/CORS/database overrides above are Python settings, not new environment
variables. Setting DEBUG/SECRET_KEY in the process ensures importing base
settings works without depending on local secret configuration. Check port
8000 is free first; stop the specific server process after E2E checks and
remove its artifact database/settings when no longer needed. Never commit
the artifact module or use these development settings in deployment.
