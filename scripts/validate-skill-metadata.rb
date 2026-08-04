#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"

ALLOWED_FRONTMATTER_KEYS = %w[name description license allowed-tools metadata].freeze
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024

def load_yaml_mapping(text, label)
  value = YAML.safe_load(text, permitted_classes: [], permitted_symbols: [], aliases: false)
  raise "#{label} must be a YAML mapping" unless value.is_a?(Hash)

  value
rescue Psych::Exception => e
  raise "invalid YAML in #{label}: #{e.message.lines.first.to_s.strip}"
end

def required_string(mapping, key, label)
  value = mapping[key]
  raise "#{label}.#{key} must be a nonempty string" unless value.is_a?(String) && !value.strip.empty?

  value.strip
end

def validate_skill(path)
  directory = File.expand_path(path)
  skill_file = File.join(directory, "SKILL.md")
  raise "SKILL.md not found" unless File.file?(skill_file)

  content = File.read(skill_file)
  match = content.match(/\A---\n(.*?)\n---(?:\n|\z)/m)
  raise "invalid or missing YAML frontmatter delimiters" unless match

  frontmatter = load_yaml_mapping(match[1], "SKILL.md frontmatter")
  non_string_keys = frontmatter.keys.reject { |key| key.is_a?(String) }
  raise "SKILL.md frontmatter keys must be strings" unless non_string_keys.empty?

  unexpected = frontmatter.keys - ALLOWED_FRONTMATTER_KEYS
  unless unexpected.empty?
    raise "unexpected SKILL.md frontmatter keys: #{unexpected.sort.join(', ')}"
  end

  name = required_string(frontmatter, "name", "SKILL.md frontmatter")
  description = required_string(frontmatter, "description", "SKILL.md frontmatter")

  raise "name must use hyphen-case" unless name.match?(/\A[a-z0-9-]+\z/)
  if name.start_with?("-") || name.end_with?("-") || name.include?("--")
    raise "name cannot start or end with a hyphen or contain consecutive hyphens"
  end
  raise "name exceeds #{MAX_NAME_LENGTH} characters" if name.length > MAX_NAME_LENGTH
  raise "folder basename must equal name '#{name}'" unless File.basename(directory) == name

  raise "description exceeds #{MAX_DESCRIPTION_LENGTH} characters" if description.length > MAX_DESCRIPTION_LENGTH
  raise "description cannot contain angle brackets" if description.include?("<") || description.include?(">")

  agent_file = File.join(directory, "agents", "openai.yaml")
  return unless File.exist?(agent_file)

  raise "agents/openai.yaml is not a file" unless File.file?(agent_file)

  agent = load_yaml_mapping(File.read(agent_file), "agents/openai.yaml")
  if agent.key?("interface")
    interface = agent["interface"]
    raise "agents/openai.yaml.interface must be a mapping" unless interface.is_a?(Hash)

    if interface.key?("display_name")
      required_string(interface, "display_name", "agents/openai.yaml.interface")
    end

    if interface.key?("short_description")
      short_description = interface["short_description"]
      unless short_description.is_a?(String) && short_description.strip.length.between?(25, 64)
        raise "agents/openai.yaml.interface.short_description must be a string of 25..64 characters"
      end
    end

    if interface.key?("default_prompt")
      default_prompt = required_string(interface, "default_prompt", "agents/openai.yaml.interface")
      invocation_tokens = default_prompt.scan(/\$[a-z0-9-]+/)
      unless invocation_tokens.include?("$#{name}")
        raise "agents/openai.yaml.interface.default_prompt must include exact invocation token $#{name}"
      end
    end
  end

  return unless agent.key?("policy")

  policy = agent["policy"]
  raise "agents/openai.yaml.policy must be a mapping" unless policy.is_a?(Hash)

  if policy.key?("allow_implicit_invocation")
    implicit = policy["allow_implicit_invocation"]
    unless implicit == true || implicit == false
      raise "agents/openai.yaml.policy.allow_implicit_invocation must be boolean"
    end
  end
end

if ARGV.empty?
  warn "Usage: #{File.basename($PROGRAM_NAME)} SKILL_DIR [SKILL_DIR ...]"
  exit 2
end

failed = false

ARGV.each do |path|
  begin
    validate_skill(path)
    puts "PASS #{path}"
  rescue StandardError => e
    failed = true
    puts "FAIL #{path}: #{e.message}"
  end
end

exit(failed ? 1 : 0)
