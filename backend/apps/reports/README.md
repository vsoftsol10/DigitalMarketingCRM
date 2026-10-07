# Insights report renderer

The report PNG endpoint uses the Playwright package pinned in the backend requirements and its matching managed Chromium build. Installing the Python package alone does not install Chromium.

After installing backend requirements, install Chromium in the same Python environment and browser cache used by the Django server:

```powershell
python -m playwright install chromium
```

For Linux deployments, install the browser and its system libraries while building the runtime image:

```sh
python -m playwright install --with-deps chromium
```

If the deployment uses a custom Playwright browser cache, set `PLAYWRIGHT_BROWSERS_PATH` for both the install command and the Django process. Restart Django after installing the browser. The renderer uses Playwright's managed Chromium and does not search for a machine-specific Chrome path.
