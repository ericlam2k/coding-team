#!/usr/bin/env node
import { access, readFile, readdir } from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const required = [
  'README.md',
  'prompts/profiles/sol.md',
  'prompts/profiles/terra.md',
  'prompts/profiles/luna.md',
  'prompts/profiles/guard.md',
  'skills/prompt-audit.md',
  'skills/prompt-compression.md',
  'skills/safety-policy-extraction.md',
  'skills/manifest.json'
];
for (const path of required) await access(new URL(path, root));
const treeEntries = await readdir(root, { recursive: true });
const forbiddenArtifact = treeEntries.find((path) =>
  path.startsWith('configs/') ||
  path.startsWith('fixtures/') ||
  path.startsWith('prompts/base/') ||
  path === 'scripts/resolve-routing.mjs' ||
  path === 'skills/model-role-mapping.md'
);
if (forbiddenArtifact) {
  throw new Error(`Forbidden compatibility artifact exists: ${forbiddenArtifact}`);
}

const manifest = JSON.parse(await readFile(new URL('../skills/manifest.json', import.meta.url)));
const selection = manifest.selection ?? {};
const invariantChecks = [
  [manifest.mode === 'optional_prompt_overlay', 'mode must be optional_prompt_overlay'],
  [manifest.routingAuthority === 'coding-team-core', 'core must be sole routing authority'],
  [manifest.runtimeIntegrated === false, 'runtime integration must remain false'],
  [selection.startsUnloaded === true, 'overlay must start unloaded'],
  [selection.selectedBy === 'lead-after-core-routing', 'Lead must select only after core routing'],
  [selection.maxOptionalWorkflows === 1, 'at most one optional workflow is allowed'],
  [selection.requireWorkflowCompatibilityWithRoutedTask === true, 'workflow compatibility with the routed task is required'],
  [selection.maxAdditionalModelCalls === 0, 'overlay must add zero model calls'],
  [selection.automaticProfileCalls === false, 'automatic profile calls must be disabled'],
  [selection.automaticStageCalls === false, 'automatic stages must be disabled'],
  [selection.automaticGuardCalls === false, 'automatic Guard calls must be disabled'],
  [selection.profilesFollowActualModelPoolSelection === true, 'profiles must follow actual core model selection']
];
for (const [ok, message] of invariantChecks) if (!ok) throw new Error(message);

const profileIds = manifest.profiles?.map(({ id }) => id).sort();
const workflowIds = manifest.workflows?.map(({ id }) => id).sort();
if (JSON.stringify(profileIds) !== JSON.stringify(['guard', 'luna', 'sol', 'terra'])) throw new Error('Profile set is incompatible');
if (JSON.stringify(workflowIds) !== JSON.stringify(['prompt-audit', 'prompt-compression', 'safety-policy-extraction'])) throw new Error('Workflow set is incompatible');
if (manifest.profiles.find(({ id }) => id === 'guard')?.kind !== 'in-call-checklist') throw new Error('Guard must remain an in-call checklist');
for (const item of [...manifest.profiles, ...manifest.workflows]) await access(new URL(`../${item.path}`, import.meta.url));
for (const workflow of manifest.workflows) {
  if (workflow.load !== 'lead-explicit-after-core-routing') throw new Error(`Workflow auto-load risk: ${workflow.id}`);
}

console.log(`Compatibility validation passed: ${required.length} retained files, ${manifest.workflows.length} optional workflows, zero additional calls.`);
