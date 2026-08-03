# Undetected

![PyPI - Version](https://img.shields.io/pypi/v/undetected) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/undetected) ![License](https://img.shields.io/pypi/l/undetected) ![Downloads](https://img.shields.io/pypi/dm/undetected)

A Selenium Chrome drop-in that hardens automation against common bot checks.

It patches the chromedriver binary (CDC / `test-type=webdriver`) and applies page-level stealth scripts on every `uc.Chrome()` session (CDP leak cleanup, `navigator.webdriver`, chrome runtime, iframes, WebGL, and more).

**Note:** Fork of [`undetected-chromedriver`](https://github.com/ultrafunkamsterdam/undetected-chromedriver). Results vary - these patches help, but they are not a guarantee against every detector.

## Installation

```bash
pip install undetected
```

## Simple Usage

```python
import undetected as uc

driver = uc.Chrome()
driver.get("https://bot.sannysoft.com/")
driver.quit()
```

Stealth runs automatically. For extra control:

```python
from undetected import apply_stealth

apply_stealth(driver, languages=["en-US", "en"], fix_hairline=True)
```

## Example Usage with Multi-Processing (doesn't work great on Windows)

```python
import undetected as uc
from undetected.patcher import Patcher
from multiprocessing import Process

def worker(idx: int):
    driver = uc.Chrome(user_multi_procs=True)
    driver.get("https://example.com")
    driver.quit()

if __name__ == "__main__":
    Patcher.patch()  # patching a unique undetected chromedriver

    processes = [Process(target=worker, args=(i,)) for i in range(4)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
```

## Example Usage with Multi-Threading

```python
import undetected as uc
from undetected.patcher import Patcher
import threading

def worker(idx: int):
    driver = uc.Chrome(user_multi_procs=True)
    driver.get("https://example.com")
    driver.quit()

if __name__ == "__main__":
    Patcher.patch()  # patching a unique undetected chromedriver

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
```
