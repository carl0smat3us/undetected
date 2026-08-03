// Keep navigator.webdriver false inside iframes without Proxy-wrapping contentWindow.

() => {
  utils.preloadCache()
  const replaceGetter = utils.replaceGetter

  const patchNavigator = (nav) => {
    if (!nav) {
      return
    }
    const proto = Object.getPrototypeOf(nav)
    const desc = Object.getOwnPropertyDescriptor(proto, 'webdriver')
    if (desc && typeof desc.get === 'function' && nav.webdriver === false) {
      return
    }
    replaceGetter(proto, 'webdriver', function webdriver() {
      return false
    })
  }

  const patchWindow = (win) => {
    if (!win) {
      return
    }
    try {
      patchNavigator(win.navigator)
    } catch (_) {}
  }

  const iframeProto = HTMLIFrameElement.prototype
  const contentWindowDesc = Object.getOwnPropertyDescriptor(iframeProto, 'contentWindow')
  if (contentWindowDesc && typeof contentWindowDesc.get === 'function') {
    const nativeGet = contentWindowDesc.get
    replaceGetter(iframeProto, 'contentWindow', function contentWindow() {
      const win = nativeGet.call(this)
      patchWindow(win)
      return win
    })
  }

  patchWindow(globalThis)

  const patchIframe = (iframe) => {
    if (!iframe) {
      return
    }
    try {
      patchWindow(iframe.contentWindow)
    } catch (_) {}
  }

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node instanceof HTMLIFrameElement) {
          patchIframe(node)
        } else if (node.querySelectorAll) {
          for (const iframe of node.querySelectorAll('iframe')) {
            patchIframe(iframe)
          }
        }
      }
    }
  })

  observer.observe(document.documentElement, { childList: true, subtree: true })
  for (const iframe of document.querySelectorAll('iframe')) {
    patchIframe(iframe)
  }
}