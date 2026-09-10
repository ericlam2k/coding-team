"""Bounded, non-shell terminal execution for compact context receipts."""

from __future__ import annotations

import math
import os
import selectors
import signal
import subprocess
import time
import codecs
from collections import deque
from typing import Sequence


CTERM_ARGV = "CTERM-ARGV"
CTERM_TIMEOUT_VALUE = "CTERM-TIMEOUT-VALUE"
CTERM_SPAWN = "CTERM-SPAWN"
CTERM_DECODE = "CTERM-DECODE"
CTERM_LINE_LIMIT = "CTERM-LINE-LIMIT"
CTERM_INTERNAL = "CTERM-INTERNAL"
MAX_LINE_BYTES = 65_536
MAX_TAIL_LINES = 20
_PROCESS_GROUP_CLEANUP_CAPABILITY: bool | None = None
_ERROR_CODES = frozenset(
    {
        CTERM_ARGV,
        CTERM_TIMEOUT_VALUE,
        CTERM_SPAWN,
        CTERM_DECODE,
        CTERM_LINE_LIMIT,
        CTERM_INTERNAL,
    }
)


class CompactTerminalError(RuntimeError):
    """A private failure exposing only a stable compact-terminal code."""

    def __init__(self, code: str) -> None:
        stable_code = code if code in _ERROR_CODES else CTERM_INTERNAL
        super().__init__(stable_code)
        self.code = stable_code


def _validate_argv(argv: Sequence[str]) -> None:
    if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence):
        raise CompactTerminalError(CTERM_ARGV)
    if not argv or not all(isinstance(item, str) for item in argv):
        raise CompactTerminalError(CTERM_ARGV)
    if not any(argv) or any("\0" in item for item in argv):
        raise CompactTerminalError(CTERM_ARGV)


def _validate_timeout(timeout_s: float) -> None:
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise CompactTerminalError(CTERM_TIMEOUT_VALUE)
    if not math.isfinite(timeout_s) or timeout_s <= 0:
        raise CompactTerminalError(CTERM_TIMEOUT_VALUE)


def _signal_process_group(process: subprocess.Popen[bytes], signal_number: int) -> bool:
    global _PROCESS_GROUP_CLEANUP_CAPABILITY
    try:
        os.killpg(process.pid, signal_number)
    except ProcessLookupError:
        return True
    except PermissionError:
        _PROCESS_GROUP_CLEANUP_CAPABILITY = False
        return False
    _PROCESS_GROUP_CLEANUP_CAPABILITY = True
    return True


def _terminate_and_reap(process: subprocess.Popen[bytes]) -> None:
    group_signalled = os.name == "posix" and _signal_process_group(
        process, signal.SIGTERM
    )
    if not group_signalled and process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        if os.name == "posix" and group_signalled:
            group_signalled = _signal_process_group(process, signal.SIGKILL)
        if not group_signalled and process.poll() is None:
            process.kill()
        process.wait()
    else:
        # The direct child may exit before descendants in its session.
        if os.name == "posix" and group_signalled:
            _signal_process_group(process, signal.SIGKILL)


def _drain_pending_output(
    process: subprocess.Popen[bytes],
    selector: selectors.BaseSelector,
    decoder: codecs.IncrementalDecoder,
    consume: object,
) -> None:
    deadline = time.monotonic() + 0.1
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not selector.select(remaining):
            return
        assert process.stdout is not None
        chunk = process.stdout.read1(65536)
        if not chunk:
            return
        consume(decoder.decode(chunk, final=False))


def execute_terminal_command(argv: Sequence[str], *, timeout_s: float) -> dict[str, object]:
    """Execute ``argv`` without a shell and return its bounded output tail."""
    _validate_argv(argv)
    _validate_timeout(timeout_s)
    try:
        process = subprocess.Popen(
            list(argv), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=False,
            start_new_session=os.name == "posix",
        )
    except (OSError, ValueError):
        raise CompactTerminalError(CTERM_SPAWN) from None

    lines: deque[str] = deque(maxlen=MAX_TAIL_LINES)
    current: list[str] = []
    current_bytes = 0
    pending_cr = False
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    selector.register(process.stdout, selectors.EVENT_READ)
    timed_out = False

    def append_line() -> None:
        nonlocal current, current_bytes
        lines.append("".join(current))
        current = []
        current_bytes = 0

    def consume(text: str) -> None:
        nonlocal current_bytes, pending_cr
        for character in text:
            if pending_cr:
                pending_cr = False
                if character == "\n":
                    continue
            if character in "\r\n":
                if character == "\r":
                    append_line()
                    pending_cr = True
                else:
                    append_line()
                continue
            current.append(character)
            current_bytes += len(character.encode("utf-8"))
            if current_bytes > MAX_LINE_BYTES:
                raise CompactTerminalError(CTERM_LINE_LIMIT)

    try:
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                _terminate_and_reap(process)
                _drain_pending_output(process, selector, decoder, consume)
                break
            events = selector.select(max(0, remaining))
            if not events:
                if process.poll() is None:
                    timed_out = True
                    _terminate_and_reap(process)
                    continue
                break
            chunk = process.stdout.read1(65536)
            if not chunk:
                selector.unregister(process.stdout)
                break
            consume(decoder.decode(chunk, final=False))
        consume(decoder.decode(b"", final=True))
        if current:
            append_line()
        process.wait()
    except CompactTerminalError:
        _terminate_and_reap(process)
        raise
    except UnicodeDecodeError:
        _terminate_and_reap(process)
        raise CompactTerminalError(CTERM_DECODE) from None
    except (OSError, ValueError):
        _terminate_and_reap(process)
        raise CompactTerminalError(CTERM_INTERNAL) from None
    finally:
        selector.close()
        if process.stdout is not None:
            process.stdout.close()

    return {"exit_code": None if timed_out else process.returncode, "last_lines": list(lines)}
