// Match real Chrome MediaCapabilities results for proprietary codecs that
// Chromium/automation builds under-report.

() => {
  utils.preloadCache()
  const mediaCapabilities = navigator.mediaCapabilities
  if (!mediaCapabilities || typeof mediaCapabilities.decodingInfo !== 'function') {
    return
  }

  const KNOWN_GOOD_CONTENT_TYPE =
    /^(?:video\/mp4(?:;[^,]*codecs="[^"]*avc1[^"]*")?|audio\/(?:mp4|aac|x-m4a|mpeg)(?:;|$))/i

  const handler = {
    apply(target, ctx, args) {
      const config = args[0]
      return Reflect.apply(target, ctx, args).then((result) => {
        if (!config || typeof config !== 'object' || typeof result !== 'object') {
          return result
        }
        const video = config.video || {}
        const audio = config.audio || {}
        const contentType = (video.contentType || audio.contentType || '').trim()
        if (!KNOWN_GOOD_CONTENT_TYPE.test(contentType)) {
          return result
        }
        if (result.supported === false) {
          return { ...result, supported: true, smooth: true, powerEfficient: false }
        }
        return result
      })
    }
  }

  utils.replaceWithProxy(mediaCapabilities, 'decodingInfo', handler)
}
