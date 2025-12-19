import multiprocessing as mp
from tests import find_and_prepare_chrome
import undetected as uc


def worker(idx: int, result_queue):
    """
    Single worker that tries to start and stop Chrome.
    """
    browser_executable_path = find_and_prepare_chrome()

    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(
            options=options,
            user_multi_procs=True,
            headless=True,
            browser_executable_path=browser_executable_path,
        )

        driver.get("https://example.com")
        title = driver.title
        driver.quit()

        result_queue.put((idx, True, title))
    except Exception as e:
        result_queue.put((idx, False, str(e)))


def test_multiprocess_chromedriver():
    """
    Launch multiple processes concurrently and ensure:
    - no crashes
    - no race conditions
    - shared chromedriver works
    """

    process_count = 4  # keep small for CI
    ctx = mp.get_context("spawn")  # IMPORTANT for CI stability
    result_queue = ctx.Queue()

    processes = [
        ctx.Process(target=worker, args=(i, result_queue))
        for i in range(process_count)
    ]

    for p in processes:
        p.start()

    for p in processes:
        p.join(timeout=60)

    results = [result_queue.get(timeout=5) for _ in range(process_count)]

    failures = [r for r in results if r[1] is False]

    if failures:
        for idx, _, err in failures:
            print(f"[Process {idx}] FAILED: {err}")

    assert not failures, f"{len(failures)} process(es) failed"
