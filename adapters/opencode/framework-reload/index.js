import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const FRAMEWORK_DIRECTIVE =
  "WYSY/coding-team framework (re-anchored post-compaction): role index core/README.md " +
  "(read the relevant role card on demand); policy: core/orchestration.md, core/human-gates.md, " +
  "core/concurrency.md, core/qa-operating-model.md, core/model-routing.md. " +
  "Before implement/scope-expansion/irreversible change: issue PIC sign-off " +
  "(SA/PM/Adv/Contra/Front/Backend per domain) + final human gate; silence is never approval.";

const MAX_PENDING = 64;

// Optional diagnostic host log. Written ONLY when FRAMEWORK_RELOAD_DEBUG=1.
// By default the plugin performs NO disk writes: it mutates only the in-memory
// system prompt and uses the host logger (ctx.log). This keeps the
// "side-effect-free / no writes" guarantee real for normal operation.
const DEBUG = process.env.FRAMEWORK_RELOAD_DEBUG === "1";
const LOG_FILE = path.join(os.homedir(), ".config", "opencode", "framework-reload-plugin.log");
function fl(level, msg) {
  if (!DEBUG) return;
  try {
    fs.appendFileSync(LOG_FILE, `${new Date().toISOString()} [${level}] [framework-reload] ${msg}\n`);
  } catch {}
}

export default async function frameworkReload(ctx) {
  const pending = new Set();
  const done = new Set(); // sessions already re-anchored for the current compaction cycle
  let dropped = 0;
  const log = (level, msg) => {
    try {
      ctx?.log?.(level, `[framework-reload] ${msg}`);
    } catch {}
    fl(level, msg);
  };

  fl("info", "plugin loaded");

  function remember(sessionID, via) {
    if (done.has(sessionID)) return; // already re-anchored for this compaction cycle
    if (pending.size >= MAX_PENDING) {
      const oldest = pending.values().next().value;
      if (oldest !== undefined) {
        pending.delete(oldest);
        dropped++;
        if (dropped % 16 === 0) log("warn", `pending set full; evicted oldest (total dropped ${dropped})`);
      }
    }
    pending.add(sessionID);
    log("debug", `marked compacted session ${sessionID} via ${via} (pending=${pending.size})`);
  }

  return {
    // experimental.session.compacting fires during compaction (carries sessionID).
    // It is the primary detector; also clears any prior "done" so a genuine new
    // compaction of the same session can re-anchor again.
    "experimental.session.compacting": async (input) => {
      const sessionID = input?.sessionID;
      if (typeof sessionID === "string") {
        done.delete(sessionID);
        remember(sessionID, "experimental.session.compacting");
      }
    },
    // session.compacted is dispatched (later, after the summary is written). It is
    // deduped so the late arrival cannot cause a second injection.
    "event": async ({ event }) => {
      if (event?.type === "session.compacted") {
        const sessionID = event?.properties?.info?.id ?? event?.properties?.sessionID;
        if (typeof sessionID === "string") remember(sessionID, "session.compacted");
      }
    },
    "experimental.chat.system.transform": async (input, output) => {
      if (typeof input?.sessionID !== "string") return;
      if (!pending.has(input.sessionID)) return;
      if (!Array.isArray(output?.system) || output.system.length === 0) return;
      if (typeof output.system[0] !== "string") return;
      output.system[0] = `${output.system[0]}\n\n${FRAMEWORK_DIRECTIVE}`;
      pending.delete(input.sessionID); // unconditional
      done.add(input.sessionID); // mark re-anchored; blocks late session.compacted re-mark
      log("info", `re-anchored framework for session ${input.sessionID}`);
    },
  };
}
