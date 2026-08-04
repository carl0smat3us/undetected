// https://github.com/berstend/puppeteer-extra/blob/c44c8bb0224c6bba2554017bfb9d7a1d0119f92f/packages/puppeteer-extra-plugin-stealth/evasions/navigator.languages/index.js

(languages) => {
  utils.preloadCache()
  const list = languages || ['en-US', 'en']
  const proto = Object.getPrototypeOf(navigator)

  utils.replaceGetter(proto, 'languages', function languages() {
    return list
  })
  utils.replaceGetter(proto, 'language', function language() {
    return list[0]
  })
}