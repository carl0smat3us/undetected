from pathlib import Path

import undetected as uc
from undetected.utils.info import get_browser_info


def test_basic():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options, headless=True)

    driver.get("https://www.google.com/")
    title = driver.title

    driver.quit()

    assert title, "Title should not be empty"


def test_basic_manual_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    zipped_driver = uc.Patcher.fetch_package(
        uc.Patcher.fetch_release_number(get_browser_info()["browser_main_version"])
    )

    driver_path = uc.Patcher.unzip_package(zipped_driver, Path(zipped_driver).parent)

    driver = uc.Chrome(
        options=options, headless=True, driver_executable_path=driver_path
    )

    driver.get("https://www.google.com/")
    title = driver.title

    driver.quit()

    assert title, "Title should not be empty"
