"""Selenium Chrome drop-in with chromedriver patching and page-level JS injection.

Submodules like ``undetected.inject`` and ``undetected.cdc`` are importable
without loading Selenium (used by sibling projects such as untrace).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = (
    "Chrome",
    "ChromeOptions",
    "Patcher",
    "Reactor",
    "CDP",
)

if TYPE_CHECKING:
    from .cdp import CDP as CDP
    from .chrome import Chrome as Chrome
    from .options import ChromeOptions as ChromeOptions
    from .patcher import Patcher as Patcher
    from .reactor import Reactor as Reactor


def __getattr__(name: str) -> Any:
    if name == "Chrome":
        from .chrome import Chrome

        return Chrome
    if name == "ChromeOptions":
        from .options import ChromeOptions

        return ChromeOptions
    if name == "Patcher":
        from .patcher import Patcher

        return Patcher
    if name == "Reactor":
        from .reactor import Reactor

        return Reactor
    if name == "CDP":
        from .cdp import CDP

        return CDP
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
