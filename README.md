# Undetected

Undetectable selenium chromedriver.

**Note:** This project is a fork of [`undetected-chromedriver`](https://github.com/ultrafunkamsterdam/undetected-chromedriver).

```bash
pip install undetected
```

Simple usage:

```python
import undetected as uc

driver = uc.Chrome()
driver.get("https://example.com")
driver.quit()
```

Example usage with multiprocessing:

```python
import undetected as uc
from undetected.patcher import Patcher

def worker(idx: int):
    driver = uc.Chrome()
    driver.get("https://example.com")
    driver.quit()

if __name__ == "__main__":
    Patcher.patch() # patching a unique undetected chromedriver

    processes = [mp.Process(target=worker, args=(i,)) for i in range(4)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
```

