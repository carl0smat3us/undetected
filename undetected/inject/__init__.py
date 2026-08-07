from __future__ import annotations

import json
from pathlib import Path
from typing import Any

JS_DIR = Path(__file__).parent / "js"


def _evaluation_string(fun: str, *args: Any) -> str:
    rendered = ", ".join(
        json.dumps("undefined" if arg is None else arg) for arg in args
    )
    return f"({fun})({rendered})"


def _eval_js(driver, filename: str, *args: Any) -> None:
    source = (JS_DIR / filename).read_text(encoding="utf-8")
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": _evaluation_string(source, *args)},
    )


def _eval_js_raw(driver, source: str) -> None:
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": source},
    )


def _user_agent_override(
    driver,
    user_agent: str | None = None,
    language: str | None = None,
    platform: str | None = None,
) -> None:
    if user_agent is None:
        ua = driver.execute_cdp_cmd("Browser.getVersion", {})["userAgent"]
    else:
        ua = user_agent
    ua = ua.replace("HeadlessChrome", "Chrome")
    override: dict[str, str] = {"userAgent": ua}
    if language:
        override["acceptLanguage"] = language
    if platform:
        override["platform"] = platform
    driver.execute_cdp_cmd("Network.setUserAgentOverride", override)


def normalize_languages(raw: list[str] | tuple[str, ...] | str | None) -> list[str]:
    """Normalize language tags for navigator.languages / Accept-Language."""
    parts: list[str] = []
    if isinstance(raw, (list, tuple)):
        for item in raw:
            tag = str(item).strip().split(";", 1)[0].strip()
            if tag:
                parts.append(tag)
    elif raw:
        for chunk in str(raw).split(","):
            tag = chunk.strip().split(";", 1)[0].strip()
            if tag:
                parts.append(tag)

    if not parts:
        return ["en-US", "en"]
    if len(parts) == 1 and "-" in parts[0]:
        primary = parts[0]
        return [primary, primary.split("-", 1)[0]]
    return parts


def inject(
    driver,
    *,
    user_agent: str | None = None,
    languages: list[str] | None = None,
    vendor: str = "Google Inc.",
    platform: str | None = None,
    webgl_vendor: str = "Intel Inc.",
    renderer: str = "Intel Iris OpenGL Engine",
    fix_hairline: bool = True,
    run_on_insecure_origins: bool = False,
    custom_js: str | None = None,
) -> None:
    """Inject page-level scripts via CDP (called by Chrome.__init__)."""
    langs = normalize_languages(languages)
    ua_languages = ",".join(langs)

    _eval_js(driver, "utils.js")
    _eval_js(driver, "navigator.userAgent.js")
    _eval_js(driver, "navigator.headless.js")
    _eval_js(driver, "cdp.js")
    _eval_js(driver, "akamai.js")
    _eval_js(driver, "sourceurl.js")
    _eval_js(driver, "navigator.webdriver.js")
    _eval_js(driver, "chrome.app.js")
    _eval_js(driver, "chrome.runtime.js", run_on_insecure_origins)
    _eval_js(driver, "chrome.csi.js")
    _eval_js(driver, "chrome.loadTimes.js")
    _eval_js(driver, "iframe.contentWindow.js")
    _eval_js(driver, "iframe.webdriver.js")
    _eval_js(driver, "media.codecs.js")
    _eval_js(driver, "media.capabilities.js")
    _eval_js(driver, "media.devices.js")
    _eval_js(driver, "media.audio.js")
    _eval_js(driver, "navigator.languages.js", langs)
    _eval_js(driver, "navigator.permissions.js")
    _eval_js(driver, "navigator.plugins.js")
    _eval_js(driver, "navigator.vendor.js", vendor)
    _eval_js(driver, "webgl.vendor.js", webgl_vendor, renderer)
    _eval_js(driver, "window.outerdimensions.js")
    if fix_hairline:
        _eval_js(driver, "hairline.fix.js")
    if custom_js:
        _eval_js_raw(driver, custom_js)
    _eval_js(driver, "cleanup.js")

    _user_agent_override(driver, user_agent, ua_languages, platform)
