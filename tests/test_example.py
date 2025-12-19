import base64
import logging
import os
from pathlib import Path

import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from tests import find_and_prepare_chrome, logger
import undetected as uc

if os.name == "nt":
    tmp_path = Path("C:/temp/screenshots")
else:
    tmp_path = Path("/tmp/screenshots")

tmp_path.mkdir(parents=True, exist_ok=True)

def test_example():
    browser_executable_path = find_and_prepare_chrome()

    driver = uc.Chrome(
        headless=True,
        browser_executable_path=browser_executable_path,
    )

    logging.getLogger().setLevel(10)

    driver.get("chrome://version")
    driver.save_screenshot(tmp_path / "versioninfo.png")

    driver.get("chrome://settings/help")
    driver.save_screenshot(tmp_path / "helpinfo.png")

    driver.get("https://www.google.com")
    driver.save_screenshot(tmp_path / "google.com.png")

    driver.get("https://bot.incolumitas.com/#botChallenge")

    pdfdata = driver.execute_cdp_cmd("Page.printToPDF", {})
    if pdfdata and "data" in pdfdata:
        buffer = base64.b64decode(pdfdata["data"])
        with open(tmp_path / "report.pdf", "wb") as f:
            f.write(buffer)

    driver.get("https://www.nowsecure.nl")

    logger.info("current url %s", driver.current_url)

    try:
        WebDriverWait(driver, 15).until(EC.title_contains("moment"))
    except TimeoutException:
        pass

    logger.info("current page source:\n%s", driver.page_source)
    logger.info("current url %s", driver.current_url)

    try:
        WebDriverWait(driver, 15).until(EC.title_contains("nowSecure"))
        logger.info("PASSED CLOUDFLARE!")
    except TimeoutException:
        logger.info("timeout")
        print(driver.current_url)

    logger.info("current page source:\n%s\n", driver.page_source)

    driver.save_screenshot(tmp_path / "nowsecure.png")

    logger.info("All screenshots and PDF saved in temporary folder: %s", tmp_path)

    driver.quit()
