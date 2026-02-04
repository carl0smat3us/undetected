# Undetected

![PyPI - Version](https://img.shields.io/pypi/v/undetected) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/undetected) ![License](https://img.shields.io/pypi/l/undetected) ![Downloads](https://img.shields.io/pypi/dm/undetected)

Undetectable selenium chromedriver.

**Warning:** The main logic of this project is to patch the ChromeDriver binary to avoid detection by anti-bot services. And this is achieved by modifying the chromedriver binary, just that. So please don't equivocate yourself by thinking that just by installing this package you will be 99.9% undetected, no you won't. If you are being detected you'll need to investigate by yourself what's causing it, it can be the package issue, but 70% of the time it's not, and if you still think its the package issue you can open an issue to explain by details whats going on.

**Note:** This project is a fork of [`undetected-chromedriver`](https://github.com/ultrafunkamsterdam/undetected-chromedriver).

## Installation

```bash
pip install undetected
````

## Simple Usage

```python
import undetected as uc

driver = uc.Chrome()
driver.get("https://example.com")
driver.quit()
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
