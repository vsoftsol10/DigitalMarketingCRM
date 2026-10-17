# Insights report renderer

The report PNG endpoint uses the Playwright package pinned in the backend requirements and its matching managed Chromium build. Installing the Python package alone does not install Chromium.

After installing backend requirements, install Chromium in the same Python environment and browser cache used by the Django server:

```powershell
python -m playwright install chromium
```

## Render deployment

The repository has no Render Blueprint, so the service's build command is configured in the Render Dashboard. Set it to the build script below so every deploy installs the Chromium version matching the pinned Playwright package, along with Chromium's Linux system dependencies:

```sh
bash render-build.sh
```

This command assumes the Render service root directory is `backend`. If the service root directory is the repository root, use `bash backend/render-build.sh` instead. Keep the existing start command unchanged. The script installs backend requirements, installs Gunicorn, installs Chromium and its Linux dependencies, and then runs `collectstatic` followed by `migrate`, matching the existing deployment steps and order.

The equivalent manual Linux install command is:

```sh
python -m playwright install --with-deps chromium
```

If the deployment uses a custom Playwright browser cache, set `PLAYWRIGHT_BROWSERS_PATH` for both the install command and the Django process. Restart Django after installing the browser. The renderer uses Playwright's managed Chromium and does not search for a machine-specific Chrome path.
