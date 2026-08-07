// Keep the media device list realistic: headless/automation builds and bare
// VMs often expose no audio output, which real Chrome always has.

() => {
  utils.preloadCache()
  const mediaDevices = navigator.mediaDevices
  if (!mediaDevices || typeof mediaDevices.enumerateDevices !== 'function') {
    return
  }

  const native = mediaDevices.enumerateDevices
  const patched = async function enumerateDevices() {
    const devices = await Reflect.apply(native, mediaDevices, [])
    if (devices.some((device) => device.kind === 'audiooutput')) {
      return devices
    }
    return [
      { deviceId: 'default', kind: 'audiooutput', label: '', groupId: 'default' },
      ...devices
    ]
  }

  utils.replaceProperty(mediaDevices, 'enumerateDevices', {
    configurable: true,
    enumerable: true,
    writable: true,
    value: patched
  })
  utils.patchToString(patched, 'function enumerateDevices() { [native code] }')
}
