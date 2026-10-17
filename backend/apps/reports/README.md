# Insights report renderer

The report PNG endpoint uses the Playwright package pinned in the backend requirements and its matching managed Chromium build. Installing the Python package alone does not install Chromium.

After installing backend requirements, install Chromium in the same Python environment and browser cache used by the Django server:

```powershell
python -m playwright install chromium
```

## Render deployment

The repository has no Render Blueprint, so the service's build command is configured in the Render Dashboard. Set the service environment variable `PLAYWRIGHT_BROWSERS_PATH` to `0` so both the build process and Gunicorn use Playwright's package-local browser directory. The build script requires this setting, installs the Chromium version matching the pinned Playwright package without `--with-deps` (which requires root privileges unavailable in this Render build environment), and launches Chromium once as a build-time check. Missing Linux shared libraries fail the build visibly before `collectstatic` or `migrate`:

```sh
bash render-build.sh
```

This command assumes the Render service root directory is `backend`. If the service root directory is the repository root, use `bash backend/render-build.sh` instead. Keep the existing start command unchanged. The script installs backend requirements, installs Gunicorn and Chromium, checks that Chromium can launch, and then runs `collectstatic` followed by `migrate`, matching the existing deployment steps and order.

The equivalent browser-only Linux install command is:

```sh
python -m playwright install chromium
```

Playwright's default Linux browser cache is under the process home directory. A build-time install and a later runtime can therefore see different caches even if the smoke check passed. The value `0` directs Playwright to install the browser alongside its Python package, tying discovery to the installed Playwright environment. The same Render environment variable must be available to any separate Celery worker or beat service that may use Playwright. The renderer uses Playwright's managed Chromium and does not search for a machine-specific Chrome path.

Render's native runtime uses Debian 12, which Playwright supports, but Render's published native-runtime package list does not guarantee all Chromium shared libraries. The build-time launch check verifies availability in the build environment. If it fails with missing shared libraries, use a Render Docker runtime with a Playwright image pinned to the matching version, such as `mcr.microsoft.com/playwright/python:v1.63.0-noble`, and install the application requirements there. The official image includes browser binaries and system dependencies; its Python Playwright package must still match the pinned version.
