# Repository Guidelines

## Project Structure & Module Organization

This is a Django SaaS project. `manage.py` is the main entry point and `core/` contains global settings, ASGI/WSGI setup, and root URL routing. Feature code is split into Django apps: `accounts/` handles the custom user model, email authentication, dashboards, forms, services, and background tasks; `plans/` handles plans, subscriptions, payment webhook views, and plan-access middleware. Shared HTML lives in `templates/`, with app-specific pages under `templates/accounts/` and email templates under `templates/email/`. `staticfiles/` contains collected/static admin assets and should not be treated as primary source for custom UI changes.

## Build, Test, and Development Commands

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run database migrations with `python manage.py migrate`. Start the local server with `python manage.py runserver`; the login page is available at `http://127.0.0.1:8000/auth/login/`. Use `python manage.py check` before committing to catch Django configuration issues. For production-style static collection, use `python manage.py collectstatic`.

## Coding Style & Naming Conventions

Follow standard Django/Python conventions: 4-space indentation, `snake_case` for functions and variables, `PascalCase` for classes and models, and descriptive template names such as `password_reset_done.html`. Keep views thin when possible; move reusable business logic into app-level service modules such as `accounts/services.py`. Keep URL names namespaced by app, for example `accounts:dashboard`.

## Testing Guidelines

There is no committed test suite yet. Add tests inside each app, preferably in `accounts/tests.py`, `plans/tests.py`, or a `tests/` package if the app grows. Use Django's test runner:

```bash
python manage.py test
```

Name test methods for behavior, such as `test_login_accepts_email_backend` or `test_zouti_webhook_activates_paid_plan`. Cover models, middleware, webhook handling, and permission-sensitive dashboard views before changing those areas.

## Commit & Pull Request Guidelines

The current history only shows `Initial commit`, so use clear imperative commit messages going forward, for example `Add Zouti webhook validation` or `Fix plan dashboard metrics`. Pull requests should include a short summary, migration notes if models changed, test/check results, linked issues when applicable, and screenshots for template or dashboard UI changes.

## Security & Configuration Tips

Do not commit `.env`, database files, logs, or secrets. Local configuration is read from environment variables via `python-decouple`; define production values for `DJANGO_SECRET_KEY`, `DEBUG=False`, allowed hosts, database credentials, SendPulse keys, and `ZOUTI_WEBHOOK_SECRET`. Be careful when editing `core/settings.py`, since debug mode controls the SQLite/PostgreSQL database selection.
