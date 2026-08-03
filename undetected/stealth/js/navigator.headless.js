// Hide navigator.headless when Chrome exposes it (headless builds).

() => {
  utils.preloadCache()
  const proto = Object.getPrototypeOf(navigator)
  if (!('headless' in navigator)) {
    return
  }
  utils.replaceGetter(proto, 'headless', function headless() {
    return false
  })
}