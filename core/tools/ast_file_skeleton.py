"""Read-only extraction of a Python file's public structural skeleton.

The helper in this module intentionally exposes only names, line numbers, and
parameter kinds.  It never imports or executes the inspected file.
"""

from __future__ import annotations

import ast
import os
import stat
from pathlib import Path
from typing import Any


_MAX_ALLOWED_BYTES = 1_048_576


class FileSkeletonError(ValueError):
    """Stable, non-sensitive failure raised by :func:`get_file_skeleton`."""

    def __init__(self, code: str, path: str | None = None) -> None:
        self.code = code
        if path is not None:
            self.path = path
        super().__init__(code)


def _path_argument(value: object) -> str:
    """Return a text path, rejecting values that could be ambiguous."""

    if isinstance(value, bool):
        raise FileSkeletonError("AST-ARGUMENT")
    try:
        text = os.fspath(value)  # type: ignore[arg-type]
    except Exception:
        raise FileSkeletonError("AST-ARGUMENT") from None
    if not isinstance(text, str) or not text:
        raise FileSkeletonError("AST-ARGUMENT")
    return text


def _resolved_root(value: object) -> Path:
    root_text = _path_argument(value)
    try:
        root = Path(root_text).resolve(strict=True)
        if not root.is_dir():
            raise FileSkeletonError("AST-ROOT")
    except FileSkeletonError:
        raise
    except (OSError, RuntimeError, ValueError):
        raise FileSkeletonError("AST-ROOT") from None
    return root


def _relative_candidate(path: object, root: Path) -> tuple[Path, str]:
    path_text = _path_argument(path)
    try:
        candidate = Path(path_text).resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        raise FileSkeletonError("AST-PATH") from None
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        raise FileSkeletonError("AST-PATH") from None
    return candidate, relative.as_posix()


def _same_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _read_source(
    candidate: Path, relative: str, max_bytes: int
) -> bytes:
    try:
        initial = candidate.stat()
    except OSError:
        raise FileSkeletonError("AST-IO", relative) from None
    if not stat.S_ISREG(initial.st_mode):
        raise FileSkeletonError("AST-TYPE", relative)
    if candidate.suffix != ".py":
        raise FileSkeletonError("AST-TYPE", relative)
    if initial.st_size > max_bytes:
        raise FileSkeletonError("AST-SIZE", relative)

    try:
        with candidate.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if not _same_identity(initial, opened):
                raise FileSkeletonError("AST-RACE", relative)
            if opened.st_size != initial.st_size:
                raise FileSkeletonError("AST-RACE", relative)
            source = handle.read(max_bytes + 1)
            final = os.fstat(handle.fileno())
            if not _same_identity(opened, final):
                raise FileSkeletonError("AST-RACE", relative)
            if final.st_size != opened.st_size:
                raise FileSkeletonError("AST-RACE", relative)
    except FileSkeletonError:
        raise
    except OSError:
        raise FileSkeletonError("AST-IO", relative) from None

    if len(source) > max_bytes or final.st_size > max_bytes:
        raise FileSkeletonError("AST-SIZE", relative)
    return source


def _parameters(arguments: ast.arguments) -> list[dict[str, str]]:
    parameters: list[dict[str, str]] = []
    parameters.extend(
        {"name": argument.arg, "kind": "positional_only"}
        for argument in getattr(arguments, "posonlyargs", ())
    )
    parameters.extend(
        {"name": argument.arg, "kind": "positional"}
        for argument in arguments.args
    )
    if arguments.vararg is not None:
        parameters.append({"name": arguments.vararg.arg, "kind": "vararg"})
    parameters.extend(
        {"name": argument.arg, "kind": "keyword_only"}
        for argument in arguments.kwonlyargs
    )
    if arguments.kwarg is not None:
        parameters.append({"name": arguments.kwarg.arg, "kind": "kwarg"})
    return parameters


def _function_definition(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, Any]:
    return {
        "kind": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
        "name": node.name,
        "line": node.lineno,
        "parameters": _parameters(node.args),
    }


def _definitions(tree: ast.Module) -> list[dict[str, Any]]:
    definitions: list[dict[str, Any]] = []
    function_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    for node in tree.body:
        if isinstance(node, function_types):
            definitions.append(_function_definition(node))
        elif isinstance(node, ast.ClassDef):
            methods = [
                _function_definition(member)
                for member in node.body
                if isinstance(member, function_types)
            ]
            definitions.append(
                {
                    "kind": "class",
                    "name": node.name,
                    "line": node.lineno,
                    "methods": methods,
                }
            )
    return definitions


def get_file_skeleton(
    path: str | os.PathLike[str],
    *,
    allowed_root: str | os.PathLike[str],
    max_bytes: int = _MAX_ALLOWED_BYTES,
) -> dict[str, object]:
    """Return a deterministic, non-executable skeleton for one Python file."""

    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int):
        raise FileSkeletonError("AST-ARGUMENT")
    if not 1 <= max_bytes <= _MAX_ALLOWED_BYTES:
        raise FileSkeletonError("AST-ARGUMENT")

    root = _resolved_root(allowed_root)
    candidate, relative = _relative_candidate(path, root)
    source_bytes = _read_source(candidate, relative, max_bytes)
    try:
        source = source_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise FileSkeletonError("AST-ENCODING", relative) from None
    try:
        tree = ast.parse(source, filename="<ast-file-skeleton>", mode="exec")
    except (SyntaxError, ValueError, TypeError):
        raise FileSkeletonError("AST-PARSE", relative) from None
    return {"path": relative, "definitions": _definitions(tree)}
