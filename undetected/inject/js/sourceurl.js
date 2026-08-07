// Strip chromedriver evaluation markers from stack strings (no Function.prototype patches).

() => {
  const MARKER_RE =
    /\/\/# sourceURL=\s*(?:__cfx_|__puppeteer_evaluation_script__|__playwright|__webdriver|__selenium|__driver|pptr:)[^\n]*/g
  const STACK_MARKER_RE =
    /(?:__cfx_|__puppeteer_evaluation_script__|__playwright|__webdriver|__selenium|__driver|chromedriver|selenium|pptr:evaluate)/i

  const nativeStackDesc = Object.getOwnPropertyDescriptor(Error.prototype, 'stack')
  if (!nativeStackDesc || !nativeStackDesc.get) {
    return
  }

  const nativeGet = nativeStackDesc.get
  const stackGet = function stack() {
    let stack = nativeGet.call(this)
    if (!stack || !STACK_MARKER_RE.test(stack)) {
      return stack
    }
    return stack
      .split('\n')
      .filter((line) => !STACK_MARKER_RE.test(line))
      .join('\n')
      .replace(MARKER_RE, '')
      .trimEnd()
  }
  utils.replaceGetter(Error.prototype, 'stack', stackGet)
}
