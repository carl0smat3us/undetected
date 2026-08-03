from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import undetected as uc

PAGE_TIMEOUT = 30
FPSCANNER_URL = "https://fpscanner.com/demo/"

BLOCKED_MARKERS = (
    "access denied",
    "request denied",
    "errors.edgesuite.net",
    "you don't have permission to access",
    "something went wrong",
)


def _wait(driver) -> WebDriverWait:
    return WebDriverWait(driver, PAGE_TIMEOUT)


def _body_text(driver) -> str:
    try:
        return driver.find_element(By.TAG_NAME, "body").text.strip()
    except Exception:
        return ""


def _page_content(driver) -> tuple[str, str]:
    return (driver.title or "").strip(), _body_text(driver)


def _fpscanner_failures(body: str) -> list[str]:
    if "bot detection" not in body.lower():
        return ["Bot Detection section missing from page body"]

    section = body.lower().split("bot detection", 1)[1]
    if "bot detected" in section:
        return ["FPScanner reported: Bot Detected"]

    lines = body.split("Bot Detection", 1)[1].splitlines()
    failures: list[str] = []
    for idx, line in enumerate(lines):
        if line.strip() != "DETECTED":
            continue
        label = ""
        for back in range(idx - 1, max(idx - 4, -1), -1):
            candidate = lines[back].strip()
            if candidate and candidate not in {"✕", "▼", "OK", "✓"}:
                label = candidate
                break
        failures.append(label or "unknown check")
    return failures


def _assert_fpscanner_clean(driver) -> None:
    title, body = _page_content(driver)
    combined = f"{title}\n{body}".lower()

    assert title, f"Title should not be empty (body: {body[:300]!r})"
    assert body, f"Page body should not be empty (title: {title!r})"
    assert (
        "fpscanner" in title.lower()
    ), f"Expected 'fpscanner' in title, got {title!r} (body: {body[:300]!r})"

    for marker in BLOCKED_MARKERS:
        assert (
            marker not in combined
        ), f"Page blocked — found {marker!r} (title: {title!r}, body: {body[:400]!r})"

    failures = _fpscanner_failures(body)
    assert not failures, (
        f"FPScanner bot checks failed: {failures} "
        f"(body excerpt: {body[body.lower().find('bot detection') : body.lower().find('bot detection') + 1200]!r})"
    )


def test_bot_fpscanner():
    driver = uc.Chrome(headless=True)
    try:
        driver.get(FPSCANNER_URL)
        _wait(driver).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Bot Detection")
        )
        _assert_fpscanner_clean(driver)
    finally:
        driver.quit()
