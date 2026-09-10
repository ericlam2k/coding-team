#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "optparse"
require "open3"

KNOWN_LAYERS = %w[unit component integration system_e2e acceptance regression nonfunctional].freeze
FINDING_CLASSES = %w[
  PRODUCT_DEFECT
  TEST_CONTRACT_DEFECT
  ENVIRONMENT_DEFECT
  TOOL_TRANSPORT_DEFECT
  UNKNOWN
].freeze
STATES = %w[DRAFT FROZEN_FOR_BUILD BUILDING VALIDATING TRIAGED CORRECTING REVALIDATING REVIEW COMPLETE BLOCKED].freeze
ALLOWED_TRANSITIONS = {
  "DRAFT" => ["FROZEN_FOR_BUILD", "BLOCKED"],
  "FROZEN_FOR_BUILD" => ["BUILDING", "BLOCKED"],
  "BUILDING" => ["VALIDATING", "BLOCKED"],
  "VALIDATING" => ["TRIAGED", "BLOCKED"],
  "TRIAGED" => ["CORRECTING", "REVIEW", "BLOCKED"],
  "CORRECTING" => ["REVALIDATING", "BLOCKED"],
  "REVALIDATING" => ["TRIAGED", "BLOCKED"],
  "REVIEW" => ["COMPLETE", "BLOCKED"],
  "COMPLETE" => [],
  "BLOCKED" => []
}.freeze
TIMEBOX_OUTCOMES = %w[COMPLETE TIMEOUT CANCELLED BLOCKED].freeze
COMMIT_PATTERN = /\A[0-9a-f]{7,64}\z/i

options = { repo: nil }
OptionParser.new do |parser|
  parser.banner = "Usage: validate-qa-evidence.rb MANIFEST [--repo PATH]"
  parser.on("--repo PATH", "Repository used to verify commit and clean-tree evidence") { |path| options[:repo] = path }
end.parse!

manifest_path = ARGV.shift
if manifest_path.nil? || !ARGV.empty?
  warn "Usage: validate-qa-evidence.rb MANIFEST [--repo PATH]"
  exit 2
end

errors = []
manifest = begin
  JSON.parse(File.read(manifest_path))
rescue Errno::ENOENT => e
  errors << "manifest not found: #{e.message}"
  {}
rescue JSON::ParserError => e
  errors << "invalid JSON: #{e.message}"
  {}
end

def required_hash(parent, key, errors)
  value = parent[key]
  errors << "missing object: #{key}" unless value.is_a?(Hash)
  value.is_a?(Hash) ? value : {}
end

def required_string(parent, key, errors)
  value = parent[key]
  errors << "missing string: #{key}" unless value.is_a?(String) && !value.empty?
  value.is_a?(String) ? value : ""
end

def required_boolean(parent, key, errors)
  value = parent[key]
  errors << "missing boolean: #{key}" unless value == true || value == false
  value == true
end

unless manifest.is_a?(Hash)
  errors << "manifest root must be an object"
  manifest = {}
end

errors << "schema_version must be 1" unless manifest["schema_version"] == 1
qa_required = manifest["qa_required"]
errors << "qa_required must be boolean" unless qa_required == true || qa_required == false
qa_mode = manifest["qa_mode"]
errors << "qa_mode must be standard or bounded" unless %w[standard bounded].include?(qa_mode)
if qa_required != true && qa_mode != "bounded"
  errors << "QA evidence validator requires qa_required=true or qa_mode=bounded"
end
required_string(manifest, "batch_id", errors)
state = required_string(manifest, "state", errors)
errors << "invalid state: #{state}" unless STATES.include?(state)
state_history = manifest["state_history"]
unless state_history.is_a?(Array) && !state_history.empty?
  errors << "state_history must be a non-empty array"
  state_history = []
else
  errors << "state_history must start with DRAFT" unless state_history.first == "DRAFT"
  errors << "state_history must end with state" unless state_history.last == state
  state_history.each_cons(2) do |from, to|
    errors << "invalid state transition #{from} -> #{to}" unless ALLOWED_TRANSITIONS.fetch(from, []).include?(to)
  end
end

scenario = required_hash(manifest, "scenario_baseline", errors)
scenario_status = required_string(scenario, "status", errors)
scenario_id = required_string(scenario, "id", errors)
scenario_sha = scenario["sha256"]
errors << "scenario_baseline.sha256 must be non-empty when frozen" if scenario_status == "Frozen for build" && !(scenario_sha.is_a?(String) && !scenario_sha.empty?)
errors << "scenario_baseline.status must be Draft or Frozen for build" unless ["Draft", "Frozen for build"].include?(scenario_status)

scope = required_hash(manifest, "scope", errors)
errors << "scope.wip_max must be 2" unless scope["wip_max"] == 2
errors << "scope.disjoint_writes must be true" unless scope["disjoint_writes"] == true
selected_layers = scope["selected_layers"]
if qa_mode == "bounded"
  errors << "bounded scope.selected_layers must be a non-empty array" unless selected_layers.is_a?(Array) && !selected_layers.empty?
  if selected_layers.is_a?(Array)
    errors << "scope.selected_layers contains unknown layer" unless selected_layers.all? { |name| KNOWN_LAYERS.include?(name) }
    errors << "scope.selected_layers contains duplicates" unless selected_layers.uniq.length == selected_layers.length
  end
end

timebox = required_hash(manifest, "timebox", errors) if qa_mode == "bounded"
if qa_mode == "bounded"
  soft_seconds = timebox["soft_seconds"]
  hard_seconds = timebox["hard_seconds"]
  errors << "timebox.soft_seconds must be an integer from 30 to 180" unless soft_seconds.is_a?(Integer) && soft_seconds.between?(30, 180)
  errors << "timebox.hard_seconds must be an integer from soft_seconds+1 to 240" unless hard_seconds.is_a?(Integer) && soft_seconds.is_a?(Integer) && hard_seconds > soft_seconds && hard_seconds <= 240
  timebox_outcome = required_string(timebox, "outcome", errors)
  errors << "timebox.outcome is invalid" unless TIMEBOX_OUTCOMES.include?(timebox_outcome)
  stop_reason = timebox["stop_reason"]
  next_actions = timebox["next_actions"]
  errors << "timebox.next_actions must be an array" unless next_actions.is_a?(Array)
  if timebox_outcome != "COMPLETE"
    errors << "non-complete timebox requires stop_reason" unless stop_reason.is_a?(String) && !stop_reason.empty?
    errors << "non-complete timebox requires one next action" unless next_actions.is_a?(Array) && !next_actions.empty?
  end
end

layers = manifest["layers"]
unless layers.is_a?(Array)
  errors << "layers must be an array"
  layers = []
end
errors << "layers must contain at least one selected layer" if layers.empty?
layer_names = layers.map { |layer| layer.is_a?(Hash) ? layer["name"] : nil }
errors << "layers must use known layer names" unless layer_names.all? { |name| KNOWN_LAYERS.include?(name) }
errors << "layers contain duplicate names" unless layer_names.compact.uniq.length == layer_names.compact.length
if qa_mode == "bounded" && selected_layers.is_a?(Array)
  errors << "layers must exactly match scope.selected_layers" unless layer_names.sort == selected_layers.sort
end
layers.each do |layer|
  unless layer.is_a?(Hash)
    errors << "each layer must be an object"
    next
  end
  name = layer["name"]
  errors << "unknown layer: #{name}" unless KNOWN_LAYERS.include?(name)
  errors << "layer #{name} mandatory must be boolean" unless layer["mandatory"] == true || layer["mandatory"] == false
  result = layer["result"]
  errors << "layer #{name} has invalid result" unless %w[PASS FAIL BLOCKED N/A].include?(result)
  errors << "layer #{name} N/A requires skip_reason" if result == "N/A" && !(layer["skip_reason"].is_a?(String) && !layer["skip_reason"].empty?)
  errors << "mandatory layer #{name} cannot be N/A" if layer["mandatory"] == true && result == "N/A"
  if qa_mode == "bounded" && selected_layers.is_a?(Array) && selected_layers.include?(name)
    errors << "selected layer #{name} cannot be N/A" if result == "N/A"
  end
  if qa_mode == "bounded" && layer["mandatory"] == true && selected_layers.is_a?(Array) && !selected_layers.include?(name)
    errors << "mandatory layer #{name} must be selected"
  end
end

validation = required_hash(manifest, "validation", errors)
validation_result = required_string(validation, "result", errors)
errors << "validation.result is invalid" unless %w[PASS FAIL BLOCKED].include?(validation_result)
validated_commit = required_string(validation, "validated_commit", errors)
errors << "validated_commit must look like a git commit" unless validated_commit.match?(COMMIT_PATTERN)
clean_tree = required_boolean(validation, "working_tree_clean", errors)
all_findings_collected = required_boolean(validation, "all_findings_collected", errors)

findings = manifest["findings"]
unless findings.is_a?(Array)
  errors << "findings must be an array"
  findings = []
end
finding_ids = []
findings.each do |finding|
  unless finding.is_a?(Hash)
    errors << "each finding must be an object"
    next
  end
  id = required_string(finding, "id", errors)
  finding_ids << id
  required_string(finding, "scenario_id", errors)
  classification = required_string(finding, "classification", errors)
  errors << "finding #{id} has invalid classification" unless FINDING_CLASSES.include?(classification)
  status = required_string(finding, "status", errors)
  errors << "finding #{id} has invalid status" unless %w[resolved accepted_residual_risk deferred].include?(status)
  required_string(finding, "expected", errors)
  required_string(finding, "actual", errors)
  refs = finding["evidence_refs"]
  errors << "finding #{id} evidence_refs must be a non-empty array" unless refs.is_a?(Array) && !refs.empty?
  regression_refs = finding["regression_case_refs"]
  if %w[PRODUCT_DEFECT TEST_CONTRACT_DEFECT].include?(classification) && status == "resolved"
    errors << "finding #{id} requires regression_case_refs" unless regression_refs.is_a?(Array) && !regression_refs.empty?
  end
end
errors << "duplicate finding IDs" unless finding_ids.uniq.length == finding_ids.length

correlation = required_hash(manifest, "correlation", errors)
correlation_complete = required_boolean(correlation, "complete", errors)
root_cause_refs = correlation["root_cause_refs"]
errors << "correlation.root_cause_refs must be an array" unless root_cause_refs.is_a?(Array)
corrective_batch_id = correlation["corrective_batch_id"]
has_confirmed_fix = findings.any? { |finding| finding.is_a?(Hash) && %w[PRODUCT_DEFECT TEST_CONTRACT_DEFECT].include?(finding["classification"]) }
errors << "confirmed product/test defects require corrective_batch_id" if has_confirmed_fix && !(corrective_batch_id.is_a?(String) && !corrective_batch_id.empty?)

regression = required_hash(manifest, "regression", errors)
regression_result = required_string(regression, "result", errors)
errors << "regression.result is invalid" unless %w[PASS FAIL BLOCKED].include?(regression_result)
regression_refs = regression["case_refs"]
errors << "regression.case_refs must be an array" unless regression_refs.is_a?(Array)

gatekeeper = required_hash(manifest, "gatekeeper", errors)
gatekeeper_decision = required_string(gatekeeper, "decision", errors)
errors << "invalid Gatekeeper decision" unless %w[NOT_STARTED APPROVE APPROVE_WITH_NOTES REVISE BLOCK].include?(gatekeeper_decision)
reviewed_commit = gatekeeper["reviewed_commit"]
errors << "reviewed_commit must look like a git commit" if reviewed_commit.is_a?(String) && !reviewed_commit.empty? && !reviewed_commit.match?(COMMIT_PATTERN)

human_gate = required_hash(manifest, "human_gate", errors)
human_required = required_boolean(human_gate, "required", errors)
human_approved = required_boolean(human_gate, "approved", errors)
errors << "required human gate needs approved=true and a reference" if human_required && (!human_approved || !human_gate["reference"].is_a?(String) || human_gate["reference"].empty?)

is_final = %w[REVIEW COMPLETE].include?(state)
is_blocked = state == "BLOCKED"
if %w[FROZEN_FOR_BUILD BUILDING VALIDATING TRIAGED CORRECTING REVALIDATING REVIEW COMPLETE].include?(state)
  errors << "state #{state} requires scenario baseline Frozen for build" unless scenario_status == "Frozen for build"
end
if %w[TRIAGED CORRECTING REVALIDATING REVIEW COMPLETE].include?(state)
  errors << "state #{state} requires all findings collected" unless all_findings_collected
end
if %w[CORRECTING REVALIDATING].include?(state)
  errors << "state #{state} requires corrective_batch_id" unless corrective_batch_id.is_a?(String) && !corrective_batch_id.empty?
end
if qa_mode == "bounded"
  timebox_outcome = timebox["outcome"]
  errors << "non-complete timebox must end in state BLOCKED" if timebox_outcome != "COMPLETE" && !is_blocked
  if is_blocked
    errors << "BLOCKED state requires validation.result BLOCKED" unless validation_result == "BLOCKED"
    errors << "BLOCKED state requires a non-complete timebox" if timebox_outcome == "COMPLETE"
    errors << "BLOCKED state must not start Gatekeeper" unless gatekeeper_decision == "NOT_STARTED"
  elsif validation_result == "BLOCKED"
    errors << "validation.result BLOCKED requires state BLOCKED"
  end
end
if is_final
  errors << "final state requires scenario baseline Frozen for build" unless scenario_status == "Frozen for build" && !scenario_sha.to_s.empty?
  errors << "final state requires validation PASS" unless validation_result == "PASS"
  errors << "final state requires all findings collected" unless all_findings_collected
  errors << "final state requires correlation complete" unless correlation_complete
  errors << "final state requires regression PASS" unless regression_result == "PASS"
  errors << "final state requires clean working tree evidence" unless clean_tree
  errors << "final state requires Gatekeeper APPROVE or APPROVE_WITH_NOTES" unless %w[APPROVE APPROVE_WITH_NOTES].include?(gatekeeper_decision)
  errors << "Gatekeeper reviewed commit must equal TE validated commit" unless reviewed_commit == validated_commit
  if qa_mode == "bounded"
    errors << "final state requires timebox outcome COMPLETE" unless timebox["outcome"] == "COMPLETE"
  end
  layers.each do |layer|
    next unless layer.is_a?(Hash) && layer["mandatory"] == true
    errors << "final state requires mandatory layer #{layer["name"]} PASS" unless layer["result"] == "PASS"
  end
  findings.each do |finding|
    next unless finding.is_a?(Hash)
    errors << "finding #{finding["id"]} is not resolved or human-accepted" unless %w[resolved accepted_residual_risk].include?(finding["status"])
  end
end

if options[:repo] && errors.empty?
  repo = File.expand_path(options[:repo])
  unless Dir.exist?(repo)
    errors << "repository not found: #{repo}"
  else
    stdout, stderr, status = Open3.capture3("git", "-C", repo, "rev-parse", "HEAD")
    errors << "cannot resolve repository HEAD: #{stderr.strip}" unless status.success?
    head = stdout.strip
    errors << "repository HEAD #{head} does not match validated_commit #{validated_commit}" if status.success? && !head.start_with?(validated_commit)
    dirty, dirty_err, dirty_status = Open3.capture3("git", "-C", repo, "status", "--porcelain")
    errors << "cannot inspect repository status: #{dirty_err.strip}" unless dirty_status.success?
    errors << "repository working tree is dirty" if dirty_status.success? && !dirty.strip.empty?
  end
end

if errors.empty?
  if state == "BLOCKED"
    puts "BLOCKED: QA evidence recorded for #{manifest["batch_id"]}; promotion stopped (state=#{state}, mode=#{qa_mode}, scenario=#{scenario_id})"
  else
    puts "PASS: QA evidence accepted for #{manifest["batch_id"]} (state=#{state}, mode=#{qa_mode}, scenario=#{scenario_id})"
  end
  exit 0
end

warn "FAIL: QA evidence rejected for #{manifest["batch_id"] || "unknown"}"
errors.each { |error| warn "- #{error}" }
exit 1
