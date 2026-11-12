#!/usr/bin/env node

/**
 * Render a local HTML table to a high-resolution PNG with Playwright.
 *
 * Usage:
 *   node export_table_png.js [input.html] [output.png]
 */

const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

let chromium;
try {
  ({ chromium } = require("playwright"));
} catch (error) {
  console.error("Playwright is not installed.");
  console.error("Install it with: npm install --save-dev playwright");
  console.error("Then install Chromium with: npx playwright install chromium");
  process.exit(1);
}

const workspace = __dirname;
const inputPath = path.resolve(workspace, process.argv[2] || "selected_special_events.html");
const outputPath = path.resolve(workspace, process.argv[3] || "selected_special_events.png");

if (!fs.existsSync(inputPath)) {
  console.error(`Input HTML file not found: ${inputPath}`);
  process.exit(1);
}

(async () => {
  const browser = await chromium.launch();

  try {
    const page = await browser.newPage({
      viewport: { width: 1240, height: 1000 },
      deviceScaleFactor: 2,
    });

    await page.goto(pathToFileURL(inputPath).href, { waitUntil: "load" });
    await page.evaluate(() => document.fonts?.ready);

    const table = page.locator("table");
    await table.waitFor({ state: "visible" });
    await table.screenshot({
      path: outputPath,
      animations: "disabled",
    });

    console.log(`Rendered ${outputPath}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(`Could not render the table: ${error.message}`);
  process.exit(1);
});
