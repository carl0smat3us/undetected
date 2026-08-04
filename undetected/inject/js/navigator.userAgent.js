// Strip HeadlessChrome and align navigator UA with Client Hints full version.

() => {
  utils.preloadCache()
  const proto = Object.getPrototypeOf(navigator)

  const chromeFullVersion = () => {
    const match = navigator.userAgent.match(/Chrome\/([\d.]+)/)
    return match ? match[1] : null
  }

  let fullVersion = chromeFullVersion()

  const stripHeadless = (value) =>
    typeof value === 'string' ? value.replace(/HeadlessChrome/g, 'Chrome') : value

  const alignChromeVersion = (value) => {
    if (typeof value !== 'string' || !fullVersion) {
      return value
    }
    return value.replace(/Chrome\/[\d.]+/, `Chrome/${fullVersion}`)
  }

  const formatValue = (value) => alignChromeVersion(stripHeadless(value))

  const patchGetter = (prop) => {
    const current = Object.getOwnPropertyDescriptor(proto, prop)
    if (!current || typeof current.get !== 'function') {
      return
    }
    const newGet = {
      userAgent() {
        return formatValue(current.get.call(navigator))
      },
      appVersion() {
        return formatValue(current.get.call(navigator))
      }
    }[prop]
    utils.replaceGetter(proto, prop, newGet)
  }

  patchGetter('userAgent')
  patchGetter('appVersion')

  const fillHighEntropy = (values, hints) => {
    const result = { ...values }
    const hintSet = new Set(hints || [])

    if (hintSet.has('uaFullVersion') && !result.uaFullVersion && fullVersion) {
      result.uaFullVersion = fullVersion
    }
    if (hintSet.has('platformVersion') && !result.platformVersion) {
      result.platformVersion = '6.17.0'
    }
    if (hintSet.has('architecture') && !result.architecture) {
      result.architecture = navigator.userAgent.includes('x86_64') ? 'x86' : ''
    }
    if (hintSet.has('bitness') && !result.bitness) {
      result.bitness = navigator.userAgent.includes('x86_64') ? '64' : ''
    }
    if (hintSet.has('model') && result.model == null) {
      result.model = ''
    }
    if (hintSet.has('formFactor') && !result.formFactor) {
      result.formFactor = ''
    }
    if (hintSet.has('wow64') && result.wow64 == null) {
      result.wow64 = false
    }

    return result
  }

  const data = navigator.userAgentData
  if (data) {
    const dataProto = Object.getPrototypeOf(data)
    const brandsDesc = Object.getOwnPropertyDescriptor(dataProto, 'brands')
    if (brandsDesc && typeof brandsDesc.get === 'function') {
      const nativeBrands = brandsDesc.get
      utils.replaceGetter(dataProto, 'brands', function brands() {
        return nativeBrands.call(data).map((entry) => ({
          ...entry,
          brand: stripHeadless(entry.brand),
        }))
      })
    }

    if (typeof dataProto.getHighEntropyValues === 'function') {
      utils.replaceWithProxy(dataProto, 'getHighEntropyValues', {
        apply(target, thisArg, args) {
          const hints = args[0] || []
          return Reflect.apply(target, thisArg, args).then((values) =>
            fillHighEntropy(values, hints)
          )
        }
      })
    }
  }
}