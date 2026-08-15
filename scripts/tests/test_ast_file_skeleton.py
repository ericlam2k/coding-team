import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


_CODING_TEAM = Path(__file__).resolve().parents[2]
if str(_CODING_TEAM) not in sys.path:
    sys.path.insert(0, str(_CODING_TEAM))

from core.tools.ast_file_skeleton import FileSkeletonError, get_file_skeleton


class AstFileSkeletonTests(unittest.TestCase):
    def _assert_error(
        self,
        callback,
        code: str,
        *,
        relative_path: str | None = None,
        forbidden: tuple[str, ...] = (),
    ) -> None:
        with self.assertRaises(FileSkeletonError) as context:
            callback()

        error = context.exception
        self.assertEqual(error.code, code)
        self.assertEqual(getattr(error, "path", None), relative_path)
        message = str(error)
        for value in forbidden:
            self.assertNotIn(value, message)

    def test_extracts_module_definitions_and_direct_methods(self) -> None:
        source = '''\
@decorator("ignored")
def top(posonly, /, positional, *vararg, keyword_only, **kwarg):
    """ignored"""
    value = "ignored"
    def nested():
        pass

async def async_top(value: int = 1):
    await work(value)

class Example(Base):
    """ignored"""
    @decorator
    def method(self, /, value, *args, flag=True, **kwargs):
        def nested_method():
            pass

    async def async_method(cls, *, enabled):
        pass

    class Nested:
        def omitted(self):
            pass
'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "pkg" / "sample.py"
            path.parent.mkdir()
            path.write_text(source, encoding="utf-8")

            result = get_file_skeleton(path, allowed_root=root)

        self.assertEqual(set(result), {"path", "definitions"})
        self.assertEqual(result["path"], "pkg/sample.py")
        self.assertEqual(
            result["definitions"],
            [
                {
                    "kind": "function",
                    "name": "top",
                    "line": 2,
                    "parameters": [
                        {"name": "posonly", "kind": "positional_only"},
                        {"name": "positional", "kind": "positional"},
                        {"name": "vararg", "kind": "vararg"},
                        {"name": "keyword_only", "kind": "keyword_only"},
                        {"name": "kwarg", "kind": "kwarg"},
                    ],
                },
                {
                    "kind": "async_function",
                    "name": "async_top",
                    "line": 8,
                    "parameters": [
                        {"name": "value", "kind": "positional"}
                    ],
                },
                {
                    "kind": "class",
                    "name": "Example",
                    "line": 11,
                    "methods": [
                        {
                            "kind": "function",
                            "name": "method",
                            "line": 14,
                            "parameters": [
                                {"name": "self", "kind": "positional_only"},
                                {"name": "value", "kind": "positional"},
                                {"name": "args", "kind": "vararg"},
                                {"name": "flag", "kind": "keyword_only"},
                                {"name": "kwargs", "kind": "kwarg"},
                            ],
                        },
                        {
                            "kind": "async_function",
                            "name": "async_method",
                            "line": 18,
                            "parameters": [
                                {"name": "cls", "kind": "positional"},
                                {"name": "enabled", "kind": "keyword_only"},
                            ],
                        },
                    ],
                },
            ],
        )

    def test_empty_file_and_json_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "empty.py"
            path.write_text("# comments only\n", encoding="utf-8")

            first = get_file_skeleton(path, allowed_root=root)
            second = get_file_skeleton(path, allowed_root=root)

        self.assertEqual(first, {"path": "empty.py", "definitions": []})
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_accepts_source_at_the_maximum_byte_limit(self) -> None:
        maximum = 1_048_576
        prefix = b"value = 1\n#"
        source = prefix + b"#" * (maximum - len(prefix))
        self.assertEqual(len(source), maximum)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "exact-limit.py"
            path.write_bytes(source)

            result = get_file_skeleton(
                path, allowed_root=root, max_bytes=maximum
            )

        self.assertEqual(
            result,
            {"path": "exact-limit.py", "definitions": []},
        )

    def test_rejects_source_over_a_lowered_limit_without_partial_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "lowered-limit.py"
            source = b"private_value = 1\n"
            path.write_bytes(source)
            sentinel = object()
            partial = sentinel

            with self.assertRaises(FileSkeletonError) as context:
                partial = get_file_skeleton(
                    path, allowed_root=root, max_bytes=len(source) - 1
                )

        self.assertIs(partial, sentinel)
        error = context.exception
        self.assertEqual(error.code, "AST-SIZE")
        self.assertEqual(error.path, "lowered-limit.py")
        self.assertNotIn(str(root), str(error))
        self.assertNotIn(str(path), str(error))
        self.assertNotIn("private_value", str(error))

    def test_rejects_source_over_the_default_ceiling(self) -> None:
        maximum = 1_048_576
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "oversized.py"
            path.write_bytes(b"#" * (maximum + 1))

            self._assert_error(
                lambda: get_file_skeleton(path, allowed_root=root),
                "AST-SIZE",
                relative_path="oversized.py",
                forbidden=(str(root), str(path)),
            )

    def test_enforces_the_maximum_byte_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "ceiling.py"
            path.write_bytes(b"value = 1\n")

            self._assert_error(
                lambda: get_file_skeleton(
                    path, allowed_root=root, max_bytes=1_048_577
                ),
                "AST-ARGUMENT",
                forbidden=(str(root), str(path)),
            )

    def test_rejects_invalid_utf8_without_disclosing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "invalid-encoding.py"
            path.write_bytes(b"value = 1\nprivate_utf8=\xff")

            self._assert_error(
                lambda: get_file_skeleton(path, allowed_root=root),
                "AST-ENCODING",
                relative_path="invalid-encoding.py",
                forbidden=(str(root), str(path), "private_utf8"),
            )

    def test_rejects_invalid_syntax_without_disclosing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "invalid-syntax.py"
            path.write_bytes(b"def broken(:\n    private_syntax_payload\n")

            self._assert_error(
                lambda: get_file_skeleton(path, allowed_root=root),
                "AST-PARSE",
                relative_path="invalid-syntax.py",
                forbidden=(str(root), str(path), "private_syntax_payload"),
            )

    def test_rejects_empty_bool_and_non_path_arguments(self) -> None:
        class BrokenPath:
            def __fspath__(self) -> str:
                raise RuntimeError("private path payload")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sample.py"
            path.write_text("value = 1\n", encoding="utf-8")
            forbidden = (str(root), str(path), "private path payload")

            for bad_path in ("", True, None, 7, b"sample.py", BrokenPath()):
                with self.subTest(argument="path", value=repr(bad_path)):
                    self._assert_error(
                        lambda bad_path=bad_path: get_file_skeleton(
                            bad_path, allowed_root=root
                        ),
                        "AST-ARGUMENT",
                        forbidden=forbidden,
                    )

            for bad_root in ("", False, None, 7, b".", BrokenPath()):
                with self.subTest(argument="allowed_root", value=repr(bad_root)):
                    self._assert_error(
                        lambda bad_root=bad_root: get_file_skeleton(
                            path, allowed_root=bad_root
                        ),
                        "AST-ARGUMENT",
                        forbidden=forbidden,
                    )

            for bad_limit in (True, False, 0, -1, 1_048_577, 1.0, "1"):
                with self.subTest(argument="max_bytes", value=repr(bad_limit)):
                    self._assert_error(
                        lambda bad_limit=bad_limit: get_file_skeleton(
                            path, allowed_root=root, max_bytes=bad_limit
                        ),
                        "AST-ARGUMENT",
                        forbidden=forbidden,
                    )

    def test_rejects_invalid_roots_and_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            root.mkdir()
            path = root / "sample.py"
            path.write_text("value = 1\n", encoding="utf-8")
            outside = base / "outside.py"
            outside.write_text("value = 2\n", encoding="utf-8")
            root_file = base / "root-file"
            root_file.write_text("not a directory\n", encoding="utf-8")
            forbidden = (str(base), str(root), str(path), "not a directory")

            self._assert_error(
                lambda: get_file_skeleton(path, allowed_root=base / "missing-root"),
                "AST-ROOT",
                forbidden=forbidden,
            )
            self._assert_error(
                lambda: get_file_skeleton(path, allowed_root=root_file),
                "AST-ROOT",
                forbidden=forbidden,
            )
            self._assert_error(
                lambda: get_file_skeleton(root / "missing.py", allowed_root=root),
                "AST-PATH",
                forbidden=forbidden,
            )
            self._assert_error(
                lambda: get_file_skeleton(outside, allowed_root=root),
                "AST-PATH",
                forbidden=forbidden,
            )
            self._assert_error(
                lambda: get_file_skeleton(root / ".." / "outside.py", allowed_root=root),
                "AST-PATH",
                forbidden=forbidden,
            )

    def test_rejects_non_python_files_and_directories_with_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text_file = root / "notes.txt"
            text_file.write_text("private literal\n", encoding="utf-8")
            python_directory = root / "package.py"
            python_directory.mkdir()
            forbidden = (str(root), str(text_file), "private literal")

            self._assert_error(
                lambda: get_file_skeleton(text_file, allowed_root=root),
                "AST-TYPE",
                relative_path="notes.txt",
                forbidden=forbidden,
            )
            self._assert_error(
                lambda: get_file_skeleton(python_directory, allowed_root=root),
                "AST-TYPE",
                relative_path="package.py",
                forbidden=forbidden,
            )

    def test_rejects_posix_fifo_with_relative_path_without_disclosure(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation unavailable")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fifo = root / "private-fifo.py"
            try:
                os.mkfifo(fifo)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"FIFO creation unavailable: {error}")

            self._assert_error(
                lambda: get_file_skeleton(fifo, allowed_root=root),
                "AST-TYPE",
                relative_path="private-fifo.py",
                forbidden=(str(root), str(fifo), "private-fifo"),
            )

    def test_rejects_inode_replacement_before_opened_handle_fstat(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "race.py"
            replacement = root / "replacement.py"
            path.write_text(
                "def original_private_payload():\n    pass\n",
                encoding="utf-8",
            )
            replacement.write_text(
                "def replacement_private_payload():\n    pass\n",
                encoding="utf-8",
            )
            original_open = Path.open
            replaced = False

            def replace_candidate_before_open(
                candidate: Path, *args, **kwargs
            ):
                nonlocal replaced
                if not replaced:
                    os.replace(replacement, candidate)
                    replaced = True
                return original_open(candidate, *args, **kwargs)

            sentinel = object()
            partial = sentinel
            with mock.patch.object(
                Path, "open", new=replace_candidate_before_open
            ):
                with self.assertRaises(FileSkeletonError) as context:
                    partial = get_file_skeleton(path, allowed_root=root)

        self.assertIs(partial, sentinel)
        error = context.exception
        self.assertEqual(error.code, "AST-RACE")
        self.assertEqual(error.path, "race.py")
        for value in (
            str(root),
            str(path),
            "original_private_payload",
            "replacement_private_payload",
            ):
            self.assertNotIn(value, str(error))

    def test_rejects_opened_handle_size_change_without_partial_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "size-race.py"
            payload = "def private_size_race_payload():\n    pass\n"
            path.write_text(payload, encoding="utf-8")
            original_fstat = os.fstat
            fstat_calls = 0

            def report_size_change(fd: int) -> os.stat_result:
                nonlocal fstat_calls
                fstat_calls += 1
                observed = original_fstat(fd)
                if fstat_calls == 2:
                    return os.stat_result(
                        observed[:6]
                        + (observed.st_size + 1,)
                        + observed[7:]
                    )
                return observed

            sentinel = object()
            partial = sentinel
            with mock.patch.object(
                os, "fstat", side_effect=report_size_change
            ):
                with self.assertRaises(FileSkeletonError) as context:
                    partial = get_file_skeleton(path, allowed_root=root)

        self.assertIs(partial, sentinel)
        self.assertEqual(fstat_calls, 2)
        error = context.exception
        self.assertEqual(error.code, "AST-RACE")
        self.assertEqual(error.path, "size-race.py")
        for value in (str(root), str(path), payload, "private_size_race_payload"):
            self.assertNotIn(value, str(error))

    def test_rejects_candidate_open_oserror_without_disclosing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "open-error.py"
            path.write_text(
                "def private_source_payload():\n    pass\n",
                encoding="utf-8",
            )
            payload = "private_open_error_payload"
            sentinel = object()
            partial = sentinel

            with mock.patch.object(
                Path, "open", side_effect=OSError(payload)
            ):
                with self.assertRaises(FileSkeletonError) as context:
                    partial = get_file_skeleton(path, allowed_root=root)

        self.assertIs(partial, sentinel)
        error = context.exception
        self.assertEqual(error.code, "AST-IO")
        self.assertEqual(error.path, "open-error.py")
        for value in (str(root), str(path), payload, "private_source_payload"):
            self.assertNotIn(value, str(error))

    def test_rejects_symlink_escape_without_disclosing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            root.mkdir()
            outside = base / "outside.py"
            outside.write_text("private = True\n", encoding="utf-8")
            escape = root / "escape.py"
            try:
                escape.symlink_to(outside)
            except OSError as error:
                self.skipTest(f"symlink fixtures unavailable: {error}")

            self._assert_error(
                lambda: get_file_skeleton(escape, allowed_root=root),
                "AST-PATH",
                forbidden=(str(base), str(root), str(outside), "private = True"),
            )

if __name__ == "__main__":
    unittest.main()
