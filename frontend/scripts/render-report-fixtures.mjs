import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const frontendRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const fixturePath = join(
  frontendRoot,
  "src/components/reports/report.render-fixtures.json",
);
const fixtures = JSON.parse(await readFile(fixturePath, "utf8"));
const vite = await createServer({
  root: frontendRoot,
  configFile: join(frontendRoot, "vite.config.js"),
  appType: "custom",
  server: { middlewareMode: true },
  logLevel: "silent",
});

try {
  const { default: ReportDocument } = await vite.ssrLoadModule(
    "/src/components/reports/ReportDocument.jsx",
  );
  const { default: reportStyles } = await vite.ssrLoadModule(
    "/src/components/reports/report.styles.css?inline",
  );
  const cases = Object.entries(fixtures).map(([name, report]) => {
    const markup = renderToStaticMarkup(
      React.createElement(ReportDocument, { report }),
    );
    // Keep the same document wrapper and stylesheet embedding used by
    // buildDocumentHtml() in InsightsExportDialog.jsx.
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>${reportStyles}</style></head><body style="margin:0;background:#fff">${markup}</body></html>`;
    return { name, html };
  });

  process.stdout.write(JSON.stringify({ cases }));
} finally {
  await vite.close();
}
