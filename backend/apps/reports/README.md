# Insights report renderer

The report PNG endpoint uses the Playwright package pinned in the backend requirements and its matching managed Chromium build. Installing the Python package alone does not install Chromium.

After installing backend requirements, install Chromium in the same Python environment and browser cache used by the Django server:

```powershell
python -m playwright install chromium
```

## Render deployment

The repository has no Render Blueprint, so the service's build command is configured in the Render Dashboard. Set it to the build script below. It installs the Chromium version matching the pinned Playwright package without `--with-deps`, which requires root privileges unavailable in this Render build environment. It then launches Chromium once as a build-time check so missing Linux shared libraries fail the build visibly, before `collectstatic` or `migrate`:

```sh
bash render-build.sh
```

This command assumes the Render service root directory is `backend`. If the service root directory is the repository root, use `bash backend/render-build.sh` instead. Keep the existing start command unchanged. The script installs backend requirements, installs Gunicorn and Chromium, checks that Chromium can launch, and then runs `collectstatic` followed by `migrate`, matching the existing deployment steps and order.

The equivalent browser-only Linux install command is:

```sh
python -m playwright install chromium
```

Render's native runtime uses Debian 12, which Playwright supports, but Render's published native-runtime package list does not guarantee all Chromium shared libraries. The build-time launch check verifies them in the build environment. If that check reports missing libraries, do not skip the check or use `--with-deps`; use a Render Docker runtime with a Playwright image pinned to the same version, such as `mcr.microsoft.com/playwright/python:v1.63.0-noble`, and install the application requirements there. The official image includes Playwright browsers and their system dependencies.

If the deployment uses a custom Playwright browser cache, set `PLAYWRIGHT_BROWSERS_PATH` for both the install command and the Django process. Restart Django after installing the browser. The renderer uses Playwright's managed Chromium and does not search for a machine-specific Chrome path.
