import threading

import undetected as uc
from tests import logger


def worker(idx: int, results: dict, lock: threading.Lock):
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options, user_multi_procs=True, headless=True)

        driver.get("https://www.google.com/")
        title = driver.title
        driver.quit()

        with lock:
            results[idx] = (True, title)
    except Exception as e:
        with lock:
            results[idx] = (False, str(e))


def test_multiproc():
    """Shared chromedriver is patched automatically — no Patcher.patch() needed."""
    thread_count = 4
    results: dict = {}
    lock = threading.Lock()

    threads = [
        threading.Thread(target=worker, args=(i, results, lock))
        for i in range(thread_count)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)

    failures = [(idx, err) for idx, (ok, err) in sorted(results.items()) if not ok]

    if failures:
        for idx, err in failures:
            logger.debug(f"[Thread {idx}] FAILED: {err}")

    assert len(results) == thread_count, "not all workers finished"
    assert not failures, f"{len(failures)} thread(s) failed"
