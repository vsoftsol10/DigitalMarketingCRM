# Repository Guidelines

## Project Structure & Module Organization

This repository is a two-part digital marketing platform:

- `backend/` is a Django and Django REST Framework service. Project configuration lives in `backend/config/`; domain apps live in `backend/apps/` (for example, `posts`, `organizations`, and `social_accounts`). Keep migrations with their owning app.
- `frontend/` is a Vite + React application. Feature UI belongs in `frontend/src/pages/` and `components/`; API access is in `api/` and `services/`; shared state, hooks, validation, and UI constants live in their corresponding `src/` directories.
- `frontend/public/` contains static browser assets. Python dependencies are pinned in `requirements.txt` (mirrored under `backend/`).

## Build, Test, and Development Commands

Run backend commands from `backend/`:

```powershell
pip install -r requirements.txt       # install Python dependencies
python manage.py migrate              # apply database migrations
python manage.py runserver            # start the Django API
python manage.py test                 # run Django app tests
```

Run frontend commands from `frontend/`:

```powershell
npm install       # install Node dependencies
npm run dev       # start the Vite development server
npm run lint      # run ESLint over JS/JSX
npm run build     # create a production bundle in dist/
```

## Coding Style & Naming Conventions

Use four-space indentation in Python and follow Django conventions: `snake_case` for modules, functions, variables, and migration names; `PascalCase` for models, serializers, and views. Keep business logic in each app's `services.py` or `selectors.py`, rather than expanding views.

Use the existing ESLint configuration for JavaScript/JSX. Name React components and page files in `PascalCase` (for example, `OrganizationList.jsx`); use `camelCase` for functions, hooks, and utilities. Keep validation schemas in `src/validation/` and constants in `src/constants/`.

## Testing Guidelines

Add backend tests beside their app in `backend/apps/<app>/tests.py`; name test methods `test_<behavior>`. Run `python manage.py test` before opening a PR. The frontend currently has linting but no configured automated test runner; at minimum run `npm run lint` and `npm run build` after UI changes.

## Change Scope & Integrations

Inspect and reuse the existing architecture before adding models, services, integrations, OAuth flows, or token-management systems. Keep changes limited to the requested feature; do not include unrelated refactoring. Do not alter frontend UI or other user-visible behavior unless the request explicitly calls for it.

Never expose or log OAuth tokens, API keys, client secrets, or other credentials. For external publishing and background jobs, prioritize authorization checks, idempotency, safe retries, error tracking, and production reliability.

## Commit & Pull Request Guidelines

Recent history uses short, imperative summaries such as `Add Pagination to the organisationlist page` and `Complete Meta integration updates`. Keep commits focused and describe the affected feature. PRs should explain user-visible behavior, list validation performed, link relevant issues, and include screenshots for frontend changes. Never commit `.env` values, OAuth tokens, or other credentials.
