import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

function loadManifest(browser) {
  const manifestPath = join(root, "..", browser, "manifest.json");
  return JSON.parse(readFileSync(manifestPath, "utf8"));
}

function testManifest(browser) {
  const manifest = loadManifest(browser);
  assert.equal(manifest.manifest_version, 3);
  assert.equal(manifest.name, "ghost-sweep");
  assert.ok(manifest.action?.default_popup, `${browser} popup is required`);
  assert.ok(Array.isArray(manifest.permissions), `${browser} permissions are required`);
  assert.ok(manifest.permissions.includes("activeTab"));
}

testManifest("chrome");
testManifest("firefox");

console.log("Extension smoke tests passed.");
