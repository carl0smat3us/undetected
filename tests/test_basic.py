import undetected as uc


def test_basic():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options, headless=True)

    driver.get("https://example.com")
    title = driver.title

    driver.quit()

    assert title, "Title should not be empty"
