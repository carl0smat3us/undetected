// Pass the Webdriver test — return false via a native-looking getter.

() => {
  utils.preloadCache()
  const proto = Object.getPrototypeOf(navigator)
  utils.replaceGetter(proto, 'webdriver', function webdriver() {
    return false
  })
}