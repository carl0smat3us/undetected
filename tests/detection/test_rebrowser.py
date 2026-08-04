from selenium.webdriver.support.ui import WebDriverWait

import undetected as uc

PAGE_TIMEOUT = 30
REBROWSER_TEST_URL = "https://bot-detector.rebrowser.net/"

REBROWSER_OPTIONAL_NEUTRAL = frozenset(
    {"mainWorldExecution", "exposeFunctionLeak", "useragent"}
)


def _wait(driver) -> WebDriverWait:
    return WebDriverWait(driver, PAGE_TIMEOUT)


def _rebrowser_detections(driver) -> list[dict]:
    return (
        driver.execute_script(
            """
            const el = document.getElementById('detections-json');
            if (!el || !el.value) return [];
            try { return JSON.parse(el.value); } catch { return []; }
            """
        )
        or []
    )


def _rebrowser_failures(detections: list[dict]) -> list[str]:
    failures: list[str] = []
    for item in detections:
        name = item.get("type") or "?"
        rating = item.get("rating", 1)
        note = (item.get("note") or "").strip()

        if name in REBROWSER_OPTIONAL_NEUTRAL:
            if rating >= 1:
                failures.append(f"{name} failed (rating={rating}, note={note[:160]!r})")
            continue

        if rating >= 0:
            failures.append(f"{name} not green (rating={rating}, note={note[:160]!r})")
    return failures


def _trigger_rebrowser_optional_checks(driver) -> None:
    driver.execute_script(
        """
        if (typeof window.dummyFn === 'function') {
          window.dummyFn();
        }
        document.getElementById('detections-json');
        """
    )


def _wait_for_rebrowser_detections(driver) -> list[dict]:
    def ready(d) -> bool:
        detections = _rebrowser_detections(d)
        if len(detections) < 8:
            return False
        return not _rebrowser_failures(detections)

    _wait(driver).until(ready)
    return _rebrowser_detections(driver)


def test_bot_rebrowser():
    driver = uc.Chrome(headless=True)
    try:
        driver.get(REBROWSER_TEST_URL)
        _wait(driver).until(
            lambda d: d.execute_script("return typeof window.dummyFn === 'function'")
        )
        _trigger_rebrowser_optional_checks(driver)
        detections = _wait_for_rebrowser_detections(driver)
        failures = _rebrowser_failures(detections)
        assert not failures, f"rebrowser-bot-detector failures: {failures}"
    finally:
        driver.quit()
