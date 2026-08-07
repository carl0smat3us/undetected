// Selenium / chromedriver leak cleanup for Akamai-protected pages.

() => {
  const LEAK_RE =
    /^(?:\$cdc_|cdc_|__driver|__webdriver|__selenium|__fxdriver|__playwright|_\$webdriver|_\$chrome|_\$cdc|_Selenium|_selenium|calledSelenium|webdriver_|selenium_|domAutomation|domAutomationController|__\$webdriverAsyncExecutor|__lastWatir)/i

  const WINDOW_LEAKS = new Set([
    '__driver_evaluate',
    '__webdriver_evaluate',
    '__selenium_evaluate',
    '__fxdriver_evaluate',
    '__driver_unwrapped',
    '__webdriver_unwrapped',
    '__selenium_unwrapped',
    '__fxdriver_unwrapped',
    '_Selenium_IDE_Recorder',
    '_selenium',
    'calledSelenium',
    '$cdc_asdjflasutopfhvcZLmcfl_',
    '$chrome_asyncScriptInfo',
    '__$webdriverAsyncExecutor',
    'webdriver',
    '__webdriverFunc',
    'domAutomation',
    'domAutomationController',
    '__lastWatirAlert',
    '__lastWatirConfirm',
    '__lastWatirPrompt',
    '__webdriver_script_fn',
    '_WEBDRIVER_ELEM_CACHE',
    '__pwInitScripts',
    '__playwright__binding__'
  ])

  const scrubObject = (obj) => {
    if (!obj) return
    for (const key of Object.getOwnPropertyNames(obj)) {
      if (LEAK_RE.test(key) || WINDOW_LEAKS.has(key)) {
        try {
          delete obj[key]
        } catch (_) {}
      }
    }
  }

  const scrubDocumentAttrs = () => {
    const root = document.documentElement
    if (!root || !root.getAttributeNames) {
      return
    }
    for (const attr of root.getAttributeNames()) {
      if (LEAK_RE.test(attr) || /webdriver/i.test(attr)) {
        try {
          root.removeAttribute(attr)
        } catch (_) {}
      }
    }
  }

  const scrubLeaks = () => {
    scrubObject(window)
    scrubObject(document)
    if (document.documentElement) {
      scrubObject(document.documentElement)
      scrubDocumentAttrs()
    }
  }

  scrubLeaks()
  queueMicrotask(scrubLeaks)
  document.addEventListener(
    'DOMContentLoaded',
    scrubLeaks,
    { once: true }
  )
  setInterval(scrubLeaks, 50)
}
