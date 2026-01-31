# Undetected

![PyPI - Version](https://img.shields.io/pypi/v/undetected) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/undetected) ![License](https://img.shields.io/pypi/l/undetected) ![Downloads](https://img.shields.io/pypi/dm/undetected)

Undetectable selenium chromedriver.

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

## Example Usage with Multiprocessing

```python
import undetected as uc
from undetected.patcher import Patcher
import multiprocessing as mp

def worker(idx: int):
    driver = uc.Chrome(user_multi_procs=True)
    driver.get("https://example.com")
    driver.quit()

if __name__ == "__main__":
    Patcher.patch()  # patching a unique undetected chromedriver

    processes = [mp.Process(target=worker, args=(i,)) for i in range(4)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
```
