// Align AudioContext.sampleRate with the platform default: headless/VM audio
// stacks report 44100 everywhere, while headful Chrome defaults to 48000 on
// Windows/Linux and 44100 on macOS.

() => {
  utils.preloadCache()
  const Ctor = window.AudioContext || window.webkitAudioContext
  if (!Ctor) {
    return
  }

  const platform =
    (navigator.userAgentData && navigator.userAgentData.platform) ||
    navigator.platform ||
    ''
  const isMac = /mac/i.test(platform)

  const patchRate = (proto) => {
    if (!proto) {
      return
    }
    const desc = Object.getOwnPropertyDescriptor(proto, 'sampleRate')
    if (!desc || typeof desc.get !== 'function') {
      return
    }
    const nativeGet = desc.get
    utils.replaceGetter(proto, 'sampleRate', function sampleRate() {
      const rate = nativeGet.call(this)
      if (!isMac && rate === 44100) {
        return 48000
      }
      return rate
    })
  }

  patchRate(Ctor.prototype)
  if (window.webkitAudioContext && window.webkitAudioContext !== Ctor) {
    patchRate(window.webkitAudioContext.prototype)
  }
}
