"""P1 public-API tests for the dispatch message guard."""

import unittest

from adapters.codex.message_guard import DispatchGuardError, build_guarded_messages


class DispatchMessageGuardP1Tests(unittest.TestCase):
    def test_exact_order_preserves_history_and_keeps_active_request_last(self) -> None:
        history = [
            {"role": "user", "content": "Earlier request"},
            {"role": "assistant", "content": "Earlier response"},
        ]
        original_history = [dict(message) for message in history]

        result = build_guarded_messages(
            "Static policy",
            "Codebase structure",
            history,
            "Active task",
            lambda messages: 40,
        )

        self.assertEqual(
            result["messages"],
            [
                {"role": "system", "content": "Static policy"},
                {"role": "system", "content": "Codebase structure"},
                *original_history,
                {"role": "user", "content": "Active task"},
            ],
        )
        self.assertEqual(history, original_history)
        self.assertEqual(result["messages"][-1]["content"], "Active task")

    def test_counter_is_called_once_with_the_final_array(self) -> None:
        calls = []

        def counter(messages):
            calls.append([dict(message) for message in messages])
            return 12

        result = build_guarded_messages(
            "Static policy",
            "Codebase structure",
            [{"role": "assistant", "content": "History"}],
            "Active task",
            counter,
        )

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], result["messages"])

    def test_default_ceiling_allows_259999_and_rejects_260000(self) -> None:
        allowed = build_guarded_messages(
            "Static policy",
            "Codebase structure",
            [],
            "Active task",
            lambda messages: 259_999,
        )
        self.assertEqual(allowed["decision"], "ALLOW")
        self.assertEqual(allowed["token_count"], 259_999)
        self.assertEqual(allowed["platform_context_window"], 272_000)
        self.assertEqual(allowed["reserve_tokens"], 12_000)
        self.assertEqual(allowed["token_ceiling"], 260_000)

        with self.assertRaises(DispatchGuardError) as raised:
            build_guarded_messages(
                "Static policy",
                "Codebase structure",
                [],
                "Active task",
                lambda messages: 260_000,
            )
        self.assertEqual(raised.exception.code, "DMG-LIMIT")
        self.assertEqual(raised.exception.token_count, 260_000)
        self.assertEqual(raised.exception.token_ceiling, 260_000)
        self.assertEqual(raised.exception.decision, "REJECT")

    def test_prefix_digest_isolated_from_history_and_request(self) -> None:
        def build(system="Static policy", structure="Codebase structure", **kwargs):
            return build_guarded_messages(
                system,
                structure,
                kwargs.get("history", []),
                kwargs.get("request", "Active task"),
                lambda messages: 10,
                prefix_template_version=kwargs.get("version", "1.0.0"),
            )

        baseline = build()["prefix_digest"]
        self.assertEqual(
            baseline,
            build(
                history=[{"role": "user", "content": "Different history"}],
                request="Different request",
            )["prefix_digest"],
        )
        self.assertNotEqual(baseline, build(system="Static policy changed")["prefix_digest"])
        self.assertNotEqual(baseline, build(structure="Structure changed")["prefix_digest"])
        self.assertNotEqual(baseline, build(version="1.0.1")["prefix_digest"])

    def test_rejects_system_history_and_invalid_message_fields(self) -> None:
        invalid_histories = (
            [{"role": "system", "content": "Injected policy"}],
            [{"role": "tool", "content": "Not allowed"}],
            [{"role": "user", "content": ""}],
            [{"role": "user", "content": "ok", "extra": "no"}],
            "not a message sequence",
        )

        for history in invalid_histories:
            with self.subTest(history=history), self.assertRaises(DispatchGuardError) as raised:
                build_guarded_messages(
                    "Static policy", "Codebase structure", history, "Active task", lambda _: 1
                )
            expected = "DMG-HISTORY-SYSTEM" if history == invalid_histories[0] else "DMG-SCHEMA"
            self.assertEqual(raised.exception.code, expected)

    def test_rejects_empty_or_invalid_required_fields_before_counter(self) -> None:
        invalid_arguments = (
            ("", "Codebase structure", [], "Active task", {}),
            ("Static policy", None, [], "Active task", {}),
            ("Static policy", "Codebase structure", [], "", {}),
            ("Static policy", "Codebase structure", [], "Active task", {"prefix_template_version": 1}),
        )
        calls = []

        for args in invalid_arguments:
            with self.subTest(args=args), self.assertRaises(DispatchGuardError) as raised:
                build_guarded_messages(*args[:4], lambda _: calls.append("called") or 1, **args[4])
            self.assertEqual(raised.exception.code, "DMG-SCHEMA")

        self.assertEqual(calls, [])

    def test_rejects_lower_ceiling_equality_and_invalid_raised_ceiling(self) -> None:
        with self.assertRaises(DispatchGuardError) as equality:
            build_guarded_messages(
                "Static policy", "Codebase structure", [], "Active task", lambda _: 40, max_tokens=40
            )
        self.assertEqual(equality.exception.code, "DMG-LIMIT")
        self.assertEqual(equality.exception.token_count, 40)
        self.assertEqual(equality.exception.token_ceiling, 40)

        for limit in (260_001, 0, -1, True, "260000"):
            with self.subTest(limit=limit), self.assertRaises(DispatchGuardError) as raised:
                build_guarded_messages(
                    "Static policy", "Codebase structure", [], "Active task", lambda _: 1, max_tokens=limit
                )
            self.assertEqual(raised.exception.code, "DMG-TOKEN-CEILING")

    def test_custom_window_reserve_and_invalid_configurations(self) -> None:
        allowed = build_guarded_messages(
            "Static policy", "Codebase structure", [], "Active task",
            lambda _: 799, platform_context_window=1000, reserve_tokens=200,
        )
        self.assertEqual(allowed["token_ceiling"], 800)
        with self.assertRaises(DispatchGuardError) as equality:
            build_guarded_messages(
                "Static policy", "Codebase structure", [], "Active task",
                lambda _: 800, platform_context_window=1000, reserve_tokens=200,
            )
        self.assertEqual(equality.exception.code, "DMG-LIMIT")

        for options in (
            {"platform_context_window": 0},
            {"platform_context_window": 272001},
            {"platform_context_window": True},
            {"reserve_tokens": 0},
            {"reserve_tokens": 272000},
            {"reserve_tokens": False},
            {"platform_context_window": 1000, "reserve_tokens": 200, "max_tokens": 801},
        ):
            with self.subTest(options=options), self.assertRaises(DispatchGuardError) as raised:
                build_guarded_messages(
                    "Static policy", "Codebase structure", [], "Active task",
                    lambda _: 1, **options,
                )
            self.assertEqual(raised.exception.code, "DMG-TOKEN-CEILING")

    def test_rejects_missing_raising_and_invalid_counter_results(self) -> None:
        def raising_counter(_):
            raise RuntimeError("counter private detail")

        cases = (
            (None, "DMG-COUNTER-MISSING"),
            (raising_counter, "DMG-COUNTER-FAILED"),
            (lambda _: True, "DMG-COUNTER-INVALID"),
            (lambda _: -1, "DMG-COUNTER-INVALID"),
        )
        for counter, code in cases:
            with self.subTest(code=code), self.assertRaises(DispatchGuardError) as raised:
                build_guarded_messages(
                    "Static policy", "Codebase structure", [], "Active task", counter
                )
            self.assertEqual(raised.exception.code, code)
            self.assertEqual(raised.exception.decision, "REJECT")

    def test_rejects_counter_mutation_and_does_not_return_messages(self) -> None:
        def mutating_counter(messages):
            messages[-1]["content"] = "changed"
            return 1

        with self.assertRaises(DispatchGuardError) as raised:
            build_guarded_messages(
                "Static policy", "Codebase structure", [], "Active task", mutating_counter
            )
        self.assertEqual(raised.exception.code, "DMG-ORDER")
        self.assertFalse(hasattr(raised.exception, "messages"))

    def test_rejection_error_is_privacy_safe_and_has_only_contract_attributes(self) -> None:
        private_content = "private-project-identifier-7f0a"
        with self.assertRaises(DispatchGuardError) as raised:
            build_guarded_messages(
                "Static policy",
                "Codebase structure",
                [],
                private_content,
                lambda _: 260_000,
            )
        error = raised.exception
        self.assertNotIn(private_content, str(error))
        self.assertEqual(
            set(DispatchGuardError.__slots__),
            {"code", "token_count", "token_ceiling", "prefix_digest", "decision"},
        )
        self.assertEqual(error.token_count, 260_000)
        self.assertEqual(error.token_ceiling, 260_000)
        self.assertRegex(error.prefix_digest or "", r"^sha256:[0-9a-f]{64}$")

    def test_prefix_digest_is_independent_of_runtime_limits(self) -> None:
        def build(**options):
            return build_guarded_messages(
                "Static policy", "Codebase structure", [], "Active task",
                lambda _: 1, **options,
            )["prefix_digest"]

        baseline = build()
        self.assertEqual(baseline, build(max_tokens=100))
        self.assertEqual(
            baseline,
            build(platform_context_window=200000, reserve_tokens=10000),
        )

    def test_prefix_changes_invalidate_only_prefix_identity(self) -> None:
        def digest(*, prompt="Static policy", structure="Codebase structure", version="1.0.0", history=None, request="Active task"):
            return build_guarded_messages(
                prompt, structure, [] if history is None else history, request, lambda _: 1,
                prefix_template_version=version,
            )["prefix_digest"]

        baseline = digest()
        self.assertNotEqual(baseline, digest(prompt="Static policy "))
        self.assertNotEqual(baseline, digest(structure="Codebase structure "))
        self.assertNotEqual(baseline, digest(version="1.0.1"))
        self.assertEqual(
            baseline,
            digest(history=[{"role": "assistant", "content": "new history"}], request="new request"),
        )

    def test_result_has_no_cache_status_and_cache_never_changes_decision(self) -> None:
        result = build_guarded_messages(
            "Static policy", "Codebase structure", [], "Active task", lambda _: 1
        )
        self.assertNotIn("cache_status", result)
        self.assertNotIn("cache", result)
        self.assertEqual(result["decision"], "ALLOW")


if __name__ == "__main__":
    unittest.main()
