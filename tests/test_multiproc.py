import multiprocessing as mp

import undetected as uc


def worker(idx: int, result_queue):
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options, user_multi_procs=True, headless=True)

        driver.get("https://example.com")
        title = driver.title
        driver.quit()

        result_queue.put((idx, True, title))
    except Exception as e:
        result_queue.put((idx, False, str(e)))


def test_multiproc():
    process_count = 4

    ctx = mp.get_context("spawn")
    result_queue = ctx.Queue()

    processes = [
        ctx.Process(target=worker, args=(i, result_queue)) for i in range(process_count)
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
