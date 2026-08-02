#!/usr/bin/env ruby
# frozen_string_literal: true

require "open3"
require "pathname"

root = Pathname(__dir__).parent
validator = root.join("validate-qa-evidence.rb")
fixtures = Pathname(__dir__).join("fixtures")

def run_case(validator, fixture, expected)
  stdout, stderr, status = Open3.capture3("ruby", validator.to_s, fixture.to_s)
  actual = status.success? ? :pass : :fail
  unless actual == expected
    warn "#{fixture.basename}: expected #{expected}, got #{actual}\n#{stdout}#{stderr}"
    exit 1
  end
  puts "PASS #{fixture.basename}: #{actual}"
end

run_case(validator, fixtures.join("valid-final.json"), :pass)
run_case(validator, fixtures.join("invalid-missing-layer.json"), :fail)
run_case(validator, fixtures.join("invalid-commit-mismatch.json"), :fail)
run_case(validator, fixtures.join("invalid-unresolved.json"), :fail)
run_case(validator, fixtures.join("invalid-state-jump.json"), :fail)
puts "QA evidence validator tests: PASS"
