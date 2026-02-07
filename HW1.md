# Blog API — Homework 1

Build a blog REST API. Read everything before you start.

## Git

1. Create a **public** GitHub repository called `blog-api`.
2. Create a branch `hw1` and do all your work there.
3. When done, **merge** `hw1` into `main` (do **not** delete the branch).
4. Future homeworks will follow the same pattern: `hw2`, `hw3`, etc. — each merged into `main`, never deleted.

## Project Structure

Your project **must** follow this layout from day one.

- `manage.py`
- `.gitignore`
- `requirements/` — split dependencies
  - `base.txt` — shared dependencies
  - `dev.txt` — dev-only (starts with `-r base.txt`)
  - `prod.txt` — prod-only (starts with `-r base.txt`)
- `logs/` — log files (add to `.gitignore`)
- `apps/` — all Django apps
  - `users/` — custom user model, JWT authentication
  - `blog/` — posts, comments, categories, tags
- `settings/` — project-level package
  - `.env` — secrets (never commit this)
  - `conf.py` — reads `.env` via `python-decouple`, exports config variables
  - `base.py` — shared settings, imports from `conf.py`
  - `urls.py` — root URL configuration
  - `wsgi.py`
  - `asgi.py`
  - `env/` — environment overrides
    - `local.py` — imports from `base.py`, sets `DEBUG=True`, SQLite, etc.
    - `prod.py` — imports from `base.py`, sets `DEBUG=False`, PostgreSQL, etc.

`settings/` is both the Django project package (`urls.py`, `wsgi.py`, `asgi.py`) and the configuration root. `manage.py` reads `BLOG_ENV_ID` from `settings/.env` to pick `settings.env.local` or `settings.env.prod` as `DJANGO_SETTINGS_MODULE`.

Load order: `manage.py` → `settings/env/local.py` → `settings/base.py` → `settings/conf.py` → `settings/.env`.

Prefix all env variables with `BLOG_` (e.g. `BLOG_SECRET_KEY`, `BLOG_REDIS_URL`) so they don't clash with other projects.

## Apps

All apps live inside `apps/`. After `startapp`, set `name = 'apps.users'` (or `'apps.blog'`) in each `apps.py` and register them in `INSTALLED_APPS` with that full path.

- `apps.users` — custom user model, JWT authentication
- `apps.blog` — posts, comments, categories, tags

---

## Code Standards

Follow these rules throughout the project:

- **PEP 8** — use a linter (`ruff` or `flake8`).
- **Constants** — no magic strings or numbers in code. Use constants.
- **Imports** — standard library + third party first, then django rest framework, then django, then local.
- **Naming** — `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Type hints** — annotate function arguments and return types, e.g. `def get_posts_by_author(author_id: int) -> QuerySet[Post]`, `def create_user(email: str, password: str) -> User`.
- **No `print()`** — use `logging` everywhere.
- **Lazy formatting** in logger calls — `logger.info('User %s', email)`, not f-strings.

---

## Models

Before writing any code, create an **ERD (Entity-Relationship Diagram)** of all models described below. Use any tool you like (dbdiagram.io, draw.io, Mermaid, etc.). Export it as an image, add it to the repository at `docs/erd.png` (or `.svg`), and embed it in your project's `README.md`.

### `users` app — Custom User

Django's default `User` model uses `username` as the login field. We want **email** instead.

You need to:
1. Create a custom user model extending `AbstractBaseUser` + `PermissionsMixin`.
2. Create a custom manager (`BaseUserManager` subclass) with `create_user` and `create_superuser`.
3. Set `USERNAME_FIELD = 'email'`.
4. Set `AUTH_USER_MODEL = 'users.User'` in `base.py` **before** your first migration. (The model label is `users.User`, not `apps.users.User` — Django uses the app label, which is the last segment of `name`.)

**Fields:**

- `email` — `EmailField(unique=True)`, primary login field
- `first_name` — `CharField(max_length=50)`, required
- `last_name` — `CharField(max_length=50)`, required
- `is_active` — `BooleanField`, default `True`
- `is_staff` — `BooleanField`, default `False`
- `date_joined` — `DateTimeField`, auto-set on creation
- `avatar` — `ImageField`, optional (blank/null allowed)

The manager should normalize the email (lowercase) and handle password hashing.

### `blog` app

**Category:**

- `name` — `CharField(max_length=100)`, unique
- `slug` — `SlugField(unique=True)`, URL-friendly identifier

**Tag:**

- `name` — `CharField(max_length=50)`, unique
- `slug` — `SlugField(unique=True)`

**Post:**

- `author` — `ForeignKey(User)`, `on_delete=CASCADE`
- `title` — `CharField(max_length=200)`
- `slug` — `SlugField(unique=True)`
- `body` — `TextField`
- `category` — `ForeignKey(Category)`, `on_delete=SET_NULL`, null allowed
- `tags` — `ManyToManyField(Tag)`, blank allowed
- `status` — `CharField`, use `TextChoices`: `draft`, `published`
- `created_at` — `DateTimeField`, auto-set on creation
- `updated_at` — `DateTimeField`, auto-set on save

**Comment:**

- `post` — `ForeignKey(Post)`, `on_delete=CASCADE`
- `author` — `ForeignKey(User)`, `on_delete=CASCADE`
- `body` — `TextField`
- `created_at` — `DateTimeField`, auto-set on creation

---

## Authentication — JWT

Use **Simple JWT** (`djangorestframework-simplejwt`) or **Djoser** with JWT mode. Add the package to `requirements/base.txt`.

Configure DRF to use `JWTAuthentication` as the default authentication class in `base.py` (`REST_FRAMEWORK` → `DEFAULT_AUTHENTICATION_CLASSES`).

**Endpoints:**

- `POST /api/auth/register/` — no auth. Create account, return user + tokens.
- `POST /api/auth/token/` — no auth. Get access + refresh tokens (login).
- `POST /api/auth/token/refresh/` — no auth. Get new access token using refresh token.

**Register** — write a `ViewSet` with a single `create` action. Validate that passwords match, create the user, return the user data (without password) and a token pair.

**Token / Refresh** — use the built-in Simple JWT views (`TokenObtainPairView`, `TokenRefreshView`). No need to write these from scratch.

---

## Blog Endpoints

Use `ViewSet` classes and register them with a DRF `Router`. Use `lookup_field = 'slug'` for `PostViewSet`.

- `GET /api/posts/` — no auth. List published posts (paginated).
- `POST /api/posts/` — auth required. Create a new post.
- `GET /api/posts/{slug}/` — no auth. Get a single post.
- `PATCH /api/posts/{slug}/` — auth required. Update own post.
- `DELETE /api/posts/{slug}/` — auth required. Delete own post.
- `GET /api/posts/{slug}/comments/` — no auth. List comments for a post.
- `POST /api/posts/{slug}/comments/` — auth required. Add a comment.

Comments can be a nested `ViewSet` under posts (via a nested router like `drf-nested-routers`) or a `@action` on `PostViewSet` — your choice.

**Permissions:**
- Anyone can read published posts and comments.
- Only authenticated users can create posts and comments.
- Users can only edit/delete **their own** posts and comments. Write a custom permission class for this.

---

## Logging

Set up Django logging using the `LOGGING` dictionary in your settings.

### Requirements

1. **Two formatters:**
   - `simple` — level and message only (for console).
   - `verbose` — timestamp, level, logger name, module, message (for files).

2. **Handlers:**
   - `console` — `StreamHandler`, level `DEBUG`, `simple` formatter.
   - `file` — `RotatingFileHandler` → `logs/app.log`, level `WARNING`, max 5 MB, 3 backups, `verbose` formatter.

3. **Loggers:**
   - Your app loggers (`users`, `blog`) — level `DEBUG`, both handlers, `propagate=False`.
   - `django.request` — level `WARNING`, file handler, `propagate=False`.

4. **Debug-only request log:** add a handler that writes all incoming requests to `logs/debug_requests.log`. This handler must only be active when `DEBUG=True` (use the `RequireDebugTrue` filter).

5. **Use logging in your code.** Every view and serializer should log meaningful events:

For example, in `CustomUserViewSet.create()`: `logger.info('Registration attempt for email: %s', request.data.get('email'))` on entry, `logger.info('User registered: %s', user.email)` on success.

Log at least:
- Registration attempts (success and failure)
- Login attempts (success and failure)
- Post creation, update, deletion
- Exceptions (`logger.exception()`)

---

## Redis

Install Redis locally or use Docker. Add `django-redis` and `redis` to `requirements/base.txt`.

### 1. Caching

Configure Django's cache backend to use Redis. Then cache the published posts list (`GET /api/posts/`) for 60 seconds. Invalidate the cache when a post is created or updated. Use either `cache_page` or manual `cache.get` / `cache.set` — explain your choice in a comment.

### 2. Rate Limiting

Implement rate limiting using Redis (via `django-ratelimit` or your own implementation).

Apply rate limits:
- `POST /api/auth/register/` — max **5** requests per minute per IP.
- `POST /api/auth/token/` — max **10** requests per minute per IP.
- `POST /api/posts/` — max **20** requests per minute per user.

When the limit is exceeded, return `429 Too Many Requests` with body: `{"detail": "Too many requests. Try again later."}`

### 3. Pub/Sub

When a new comment is created, **publish** a JSON event to a Redis channel (`comments`).

Write a management command (`python manage.py listen_comments`) that **subscribes** to this channel and prints incoming messages to the console. No WebSockets needed — just a terminal subscriber.

---

## Checklist

- [ ] `settings/.env` is in `.gitignore`
- [ ] `logs/` is in `.gitignore`
- [ ] Settings split: `conf.py`, `base.py`, `env/local.py`, `env/prod.py`
- [ ] Requirements split: `base.txt`, `dev.txt`, `prod.txt`
- [ ] ERD image in `docs/` and embedded in `README.md`
- [ ] Custom user model with email as `USERNAME_FIELD`
- [ ] `AUTH_USER_MODEL` set in `base.py`
- [ ] Type hints on function arguments and return types
- [ ] No magic strings — constants via `TextChoices` / module-level
- [ ] JWT authentication works (register, token, refresh)
- [ ] Blog CRUD with ownership permissions
- [ ] Logging configured and used in views/serializers
- [ ] Debug request log only active when `DEBUG=True`
- [ ] Redis caching on posts list with invalidation
- [ ] Rate limiting on auth and post creation
- [ ] Pub/sub management command works
- [ ] Repository link submitted as a `.txt` file
