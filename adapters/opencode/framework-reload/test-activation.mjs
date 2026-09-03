// Repeatable proof of framework-reload runtime activation (no full OpenCode restart needed).
// Run: node adapters/opencode/framework-reload/test-activation.mjs
import { strict as assert } from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

// Hermetic home sandbox. The plugin resolves its optional debug log path via
// os.homedir() at module load ($HOME on POSIX, USERPROFILE on Windows). Point
// both at a fresh temp dir BEFORE importing index.js so this test never reads,
// destroys, or depends on the real user host log at ~/.config/opencode/.
const SANDBOX_HOME = fs.mkdtempSync(path.join(os.tmpdir(), "framework-reload-test-home-"));
process.env.HOME = SANDBOX_HOME;
process.env.USERPROFILE = SANDBOX_HOME;

const here = path.dirname(new URL(import.meta.url).pathname);
const mod = await import(pathToFileURL(path.join(here, "index.js")).href);
const frameworkReload = mod.default;
assert.equal(typeof frameworkReload, "function", "default export must be the plugin factory");

// Resolves inside SANDBOX_HOME because HOME/USERPROFILE were overridden above.
const LOG_FILE = path.join(os.homedir(), ".config", "opencode", "framework-reload-plugin.log");

const S = "ses_AUDIT";
const injected = (s) => (typeof s === "string" && s.includes("WYSY/coding-team framework (re-anchored") ? 1 : 0);

const r = await frameworkReload({ log: () => {} });

// 1. activation: experimental.session.compacting -> first transform injects exactly once
await r["experimental.session.compacting"]({ sessionID: S });
const o1 = { system: ["BASE"] };
await r["experimental.chat.system.transform"]({ sessionID: S }, o1);
assert.equal(injected(o1.system[0]), 1, "first request after compaction should inject once");

// 2. late session.compacted must NOT cause a second injection
await r["event"]({ event: { type: "session.compacted", properties: { info: { id: S } } } });
const o2 = { system: ["BASE"] };
await r["experimental.chat.system.transform"]({ sessionID: S }, o2);
assert.equal(injected(o2.system[0]), 0, "late session.compacted must not re-inject");

// 3. genuine re-compaction should re-anchor again
await r["experimental.session.compacting"]({ sessionID: S });
const o3 = { system: ["BASE"] };
await r["experimental.chat.system.transform"]({ sessionID: S }, o3);
assert.equal(injected(o3.system[0]), 1, "re-compaction should re-anchor");

// 4. edge cases (per runtime-evidence-request.md)
// 4a. empty system array -> no throw, no injection
const oE1 = { system: [] };
await r["experimental.chat.system.transform"]({ sessionID: S }, oE1);
assert.equal(injected(oE1.system[0]), 0, "empty system array must not inject/crash");

// 4b. non-string system[0] -> guard skips, untouched
const oE2 = { system: [{ not: "a string" }] };
await r["experimental.chat.system.transform"]({ sessionID: S }, oE2);
assert.equal(oE2.system[0].not, "a string", "non-string system[0] left untouched");

// 4c. missing sessionID in compacting hook -> remember not called
await r["experimental.session.compacting"]({});
// 4d. malformed event payloads -> no crash
await r["event"]({ event: { type: "other" } });
await r["event"]({});
// 4e. transform with missing sessionID -> no-op
const oE5 = { system: ["BASE"] };
await r["experimental.chat.system.transform"]({}, oE5);
assert.equal(injected(oE5.system[0]), 0, "missing sessionID transform is a no-op");

// 4f. 65 concurrent pending sessions -> eviction at MAX_PENDING=64, no crash
const r2 = await frameworkReload({ log: () => {} });
for (let i = 0; i < 65; i++) {
  await r2["experimental.session.compacting"]({ sessionID: "sess_" + i });
}
const oE3 = { system: ["BASE"] };
await r2["experimental.chat.system.transform"]({ sessionID: "sess_0" }, oE3);
assert.equal(injected(oE3.system[0]), 0, "evicted oldest (1st) session does not inject");
const oE4 = { system: ["BASE"] };
await r2["experimental.chat.system.transform"]({ sessionID: "sess_64" }, oE4);
assert.equal(injected(oE4.system[0]), 1, "65th session (within capacity after eviction) injects once");

// 5. default mode creates NO new host log file (sandbox: none existed before)
assert.equal(fs.existsSync(LOG_FILE), false, "default mode must not create a new host log file");

// 6. default mode neither destroys nor appends to a PRE-EXISTING host log.
// Simulates the reported environment where a stale user debug log already
// exists and the sandbox cannot remove it: the plugin must leave it byte-identical.
fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
const SENTINEL = "pre-existing user diagnostic log — must remain untouched\n";
fs.writeFileSync(LOG_FILE, SENTINEL);
const r3 = await frameworkReload({ log: () => {} });
await r3["experimental.session.compacting"]({ sessionID: "ses_PREEXISTING" });
const oP = { system: ["BASE"] };
await r3["experimental.chat.system.transform"]({ sessionID: "ses_PREEXISTING" }, oP);
assert.equal(injected(oP.system[0]), 1, "separate factory instance re-anchors independently");
assert.equal(
  fs.readFileSync(LOG_FILE, "utf8"),
  SENTINEL,
  "default mode must not destroy or append to a pre-existing host log",
);

// Best-effort cleanup of the sandbox home only (never the real user home).
try { fs.rmSync(SANDBOX_HOME, { recursive: true, force: true }); } catch {}

console.log("PASS: framework-reload activation proven (inject-once, no double-inject, re-anchor, edge cases) + hermetic default no-write");
