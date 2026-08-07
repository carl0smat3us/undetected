"""Shared chromedriver CDC / automation-string binary patch helpers."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Sequence

CDC_INJECTION_RE = re.compile(rb"\{window\.cdc.*?;\}")

TEST_TYPE_WEBDRIVER = b"test-type=webdriver"
ENABLE_AUTOMATION = b"enable-automation"

# Quiet NOP marker used by undetected Patcher.
UC_CDC_MARKER = b"{/*uc*/"
# Legacy / alternate markers accepted by is_binary_patched checks.
UC_PATCH_MARKERS: tuple[bytes, ...] = (UC_CDC_MARKER, b"undetected chromedriver")


def is_windows() -> bool:
    return sys.platform.startswith("win")


def default_string_blanks(*, windows: bool | None = None) -> tuple[bytes, ...]:
    """Strings to blank in chromedriver. Never blank enable-automation on Windows."""
    win = is_windows() if windows is None else windows
    if win:
        return (TEST_TYPE_WEBDRIVER,)
    return (TEST_TYPE_WEBDRIVER, ENABLE_AUTOMATION)


def blank_substrings(content: bytes, needles: Iterable[bytes]) -> bytes:
    updated = content
    for needle in needles:
        if needle in updated:
            updated = updated.replace(needle, b" " * len(needle))
    return updated


def cdc_nop_replacement(injection: bytes, marker: bytes = UC_CDC_MARKER) -> bytes:
    """Same-length CDC block replacement ending with ``}`` when possible."""
    if len(injection) < len(marker) + 1:
        return b" " * len(injection)
    return marker + (b" " * (len(injection) - len(marker) - 1)) + b"}"


def cdc_console_replacement(injection: bytes, marker_text: bytes) -> bytes:
    """``console.log("…")`` style replacement padded to the CDC block length."""
    body = b'{console.log("' + marker_text + b'")}'
    return body.ljust(len(injection), b" ")


def patch_cdc_content(
    content: bytes,
    *,
    replacement: bytes | None = None,
    marker: bytes = UC_CDC_MARKER,
    blank: Sequence[bytes] | None = None,
) -> tuple[bytes, bool]:
    """
    Replace the ``window.cdc`` injection and blank automation strings.

    Returns ``(updated_content, changed)``. If no CDC block is found, returns
    the original content and ``False``.
    """
    match = CDC_INJECTION_RE.search(content)
    if not match:
        return content, False

    injection = match[0]
    if replacement is None:
        replacement = cdc_nop_replacement(injection, marker)

    updated = content.replace(injection, replacement, 1)
    needles = default_string_blanks() if blank is None else blank
    updated = blank_substrings(updated, needles)
    return updated, updated != content


def content_has_patch_marker(content: bytes, markers: Sequence[bytes]) -> bool:
    return any(marker in content for marker in markers)
