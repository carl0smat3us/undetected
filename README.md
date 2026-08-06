# Undetected

A Selenium Chrome drop-in that hardens automation against common bot checks.

It patches the chromedriver binary (CDC / `test-type=webdriver`) and injects page-level scripts on every `uc.Chrome()` session (CDP leak cleanup, `navigator.webdriver`, chrome runtime, iframes, WebGL, and more).

**Note:** Fork of [`undetected-chromedriver`](https://github.com/ultrafunkamsterdam/undetected-chromedriver). Results vary - these patches help, but they are not a guarantee against every detector.

## Installation

```bash
pip install git+https://github.com/lovebrownie/undetected.git
```

## Simple Usage

```python
import undetected as uc

driver = uc.Chrome()
driver.get("https://bot.sannysoft.com/")
driver.quit()
```

```python
import undetected as uc

options = uc.ChromeOptions()
options.languages = ["fr-FR", "fr"]

driver = uc.Chrome(options=options)
driver.get("https://bot.sannysoft.com/")
driver.quit()
```

## Multi-Threading

```python
import undetected as uc
import threading

def worker(idx: int):
    driver = uc.Chrome(user_multi_procs=True)
    driver.get("https://www.google.com/")
    driver.quit()

if __name__ == "__main__":
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
```
