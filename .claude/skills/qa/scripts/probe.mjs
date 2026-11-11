#!/usr/bin/env node
// Read-only page probe for QA. Uses the Playwright installed in the current project.
//
//   node probe.mjs <url> [--out DIR] [--name LABEL] [--mobile] [--links] [--timeout MS]
//
// Loads the page, waits for the network to settle, and reports as JSON (stdout, and
// DIR/LABEL.json): HTTP status, load timing, LCP and CLS, console errors and warnings,
// uncaught page errors, failed requests, accessibility gaps, horizontal overflow,
// interactive elements, same-origin links. Saves a full-page screenshot DIR/LABEL.png.
// --links checks same-origin links with HEAD requests (local hosts only; never follows
// logout/delete-style links). It never clicks or submits anything.
// Exit: 0 probe ran (issues may exist), 2 bad arguments, 3 navigation failed,
// 4 Playwright missing (npm i -D playwright && npx playwright install chromium).

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name) => args.includes(name);
const value = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};
const url = args.find((a) => /^https?:\/\//.test(a) || a.startsWith("file:"));
if (!url) {
  console.error("usage: node probe.mjs <url> [--out DIR] [--name LABEL] [--mobile] [--links]");
  process.exit(2);
}
const outDir = value("--out", "artifacts/qa/probe");
const label = (value("--name", "") || new URL(url).pathname.replace(/[^a-z0-9]+/gi, "-") || "page")
  .replace(/^-+|-+$/g, "")
  .slice(0, 60) || "home";
const mobile = flag("--mobile");
const timeout = Number(value("--timeout", "30000"));

let playwright;
const req = createRequire(path.join(process.cwd(), "noop.js"));
for (const name of ["playwright", "@playwright/test", "playwright-core"]) {
  try {
    playwright = req(name);
    break;
  } catch {
    // try the next package name
  }
}
if (!playwright?.chromium) {
  console.error("probe: Playwright not found in this project. Run: npm i -D playwright && npx playwright install chromium");
  process.exit(4);
}

fs.mkdirSync(outDir, { recursive: true });
// Bundled Chromium first, then installed Chrome or Edge, so a version mismatch still works.
let browser;
const launchErrors = [];
for (const options of [{}, { channel: "chrome" }, { channel: "msedge" }]) {
  try {
    browser = await playwright.chromium.launch(options);
    break;
  } catch (error) {
    launchErrors.push(`${options.channel || "bundled"}: ${error.message.split("\n")[0]}`);
  }
}
if (!browser) {
  console.error(`probe: no browser could start (run: npx playwright install chromium)\n  ${launchErrors.join("\n  ")}`);
  process.exit(4);
}
const context = await browser.newContext(
  mobile ? { ...playwright.devices["iPhone 13"] } : { viewport: { width: 1280, height: 800 } },
);
const page = await context.newPage();
const consoleMessages = [];
const pageErrors = [];
const failedRequests = [];
page.on("console", (m) => {
  if (m.type() === "error" || m.type() === "warning") {
    consoleMessages.push({ type: m.type(), text: m.text().slice(0, 500) });
  }
});
page.on("pageerror", (e) => pageErrors.push(String(e).slice(0, 500)));
page.on("requestfailed", (r) => failedRequests.push({ url: r.url(), error: r.failure()?.errorText }));
page.on("response", (r) => {
  if (r.status() >= 400) failedRequests.push({ url: r.url(), status: r.status() });
});

const started = Date.now();
let response;
try {
  response = await page.goto(url, { waitUntil: "load", timeout });
} catch (error) {
  console.error(`probe: navigation failed: ${error.message.split("\n")[0]}`);
  await browser.close();
  process.exit(3);
}
await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => {});
const loadMs = Date.now() - started;
const shot = path.join(outDir, `${label}${mobile ? "-mobile" : ""}.png`);
await page.screenshot({ path: shot, fullPage: true });

const audit = await page.evaluate(async () => {
  const name = (el) =>
    (el.getAttribute("aria-label") || el.getAttribute("title") || el.innerText || el.value || "")
      .trim()
      .replace(/\s+/g, " ")
      .slice(0, 80);
  const labelled = (el) =>
    el.labels?.length || el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") ||
    el.getAttribute("title") || el.getAttribute("placeholder");
  const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const sel = (el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : "") +
    (el.className && typeof el.className === "string" ? `.${el.className.trim().split(/\s+/)[0]}` : "");
  const metric = (type) =>
    new Promise((resolve) => {
      let last = null;
      try {
        new PerformanceObserver((list) => {
          for (const e of list.getEntries()) last = type === "layout-shift" ? (last || 0) + (e.hadRecentInput ? 0 : e.value) : e.startTime;
        }).observe({ type, buffered: true });
      } catch {
        resolve(null);
      }
      setTimeout(() => resolve(last), 300);
    });
  const ids = [...document.querySelectorAll("[id]")].map((e) => e.id);
  const nav = performance.getEntriesByType("navigation")[0];
  return {
    title: document.title,
    lang: document.documentElement.lang || null,
    h1: document.querySelectorAll("h1").length,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
    timing: nav ? { domContentLoadedMs: Math.round(nav.domContentLoadedEventEnd), loadMs: Math.round(nav.loadEventEnd) } : null,
    lcpMs: await metric("largest-contentful-paint").then((v) => (v == null ? null : Math.round(v))),
    cls: await metric("layout-shift").then((v) => (v == null ? 0 : Number(v.toFixed(3)))),
    a11y: {
      imagesWithoutAlt: [...document.images].filter((i) => !i.hasAttribute("alt") && visible(i)).map((i) => i.currentSrc || i.src).slice(0, 20),
      unlabeledInputs: [...document.querySelectorAll("input:not([type=hidden]), select, textarea")].filter((el) => visible(el) && !labelled(el)).map(sel).slice(0, 20),
      unnamedButtonsAndLinks: [...document.querySelectorAll("button, a[href], [role=button]")].filter((el) => visible(el) && !name(el) && !el.querySelector("img[alt]:not([alt=''])")).map(sel).slice(0, 20),
      duplicateIds: [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))].slice(0, 20),
    },
    interactive: [...document.querySelectorAll("a[href], button, input, select, textarea, [role=button], [onclick]")]
      .filter(visible)
      .slice(0, 80)
      .map((el) => ({ tag: el.tagName.toLowerCase(), type: el.getAttribute("type"), name: name(el), selector: sel(el) })),
    links: [...new Set([...document.querySelectorAll("a[href]")].map((a) => a.href))]
      .filter((h) => { try { return new URL(h).origin === location.origin; } catch { return false; } })
      .slice(0, 200),
  };
});

const linkResults = [];
if (flag("--links")) {
  const host = new URL(url).hostname;
  const local = /^(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])$|\.(localhost|test)$/.test(host);
  for (const link of audit.links.slice(0, 60)) {
    if (/logout|signout|sign-out|delete|remove|destroy|unsubscribe|cancel/i.test(link)) continue;
    if (!local) {
      linkResults.push({ url: link, status: "unchecked (non-local host)" });
      continue;
    }
    try {
      const r = await context.request.fetch(link, { method: "HEAD", timeout: 8000, maxRedirects: 5 });
      linkResults.push({ url: link, status: r.status() });
    } catch (error) {
      linkResults.push({ url: link, status: `error: ${error.message.split("\n")[0]}` });
    }
  }
}
await browser.close();

const report = {
  url,
  finalUrl: page.url(),
  status: response ? response.status() : null,
  viewport: mobile ? "iPhone 13" : "1280x800",
  loadMs,
  screenshot: shot,
  consoleMessages,
  pageErrors,
  failedRequests,
  brokenLinks: linkResults.filter((l) => typeof l.status !== "number" || l.status >= 400),
  checkedLinks: linkResults.length,
  ...audit,
};
const jsonPath = path.join(outDir, `${label}${mobile ? "-mobile" : ""}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
