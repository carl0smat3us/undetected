// https://github.com/berstend/puppeteer-extra/blob/c44c8bb0224c6bba2554017bfb9d7a1d0119f92f/packages/puppeteer-extra-plugin-stealth/evasions/webgl.vendor/index.js

(vendor, renderer) => {
  const spoofVendor = vendor || 'Intel Inc.'
  const spoofRenderer = renderer || 'Intel Iris OpenGL Engine'
  const UNMASKED_VENDOR_WEBGL = 37445
  const UNMASKED_RENDERER_WEBGL = 37446

  const getParameterProxyHandler = {
    apply: function (target, ctx, args) {
      const param = (args || [])[0]
      if (param === UNMASKED_VENDOR_WEBGL) {
        return spoofVendor
      }
      if (param === UNMASKED_RENDERER_WEBGL) {
        return spoofRenderer
      }
      return utils.cache.Reflect.apply(target, ctx, args)
    }
  }

  const addProxy = (obj, propName) => {
    if (!obj) {
      return
    }
    utils.replaceWithProxy(obj, propName, getParameterProxyHandler)
  }

  addProxy(WebGLRenderingContext.prototype, 'getParameter')
  addProxy(WebGL2RenderingContext.prototype, 'getParameter')

  const workerPatch =
    `(function(){var v=${JSON.stringify(spoofVendor)};var r=${JSON.stringify(spoofRenderer)};` +
    `function p(proto){if(!proto)return;var o=proto.getParameter;proto.getParameter=function(n){` +
    `if(n===37445)return v;if(n===37446)return r;return o.apply(this,arguments);};}` +
    `p(typeof WebGLRenderingContext!=='undefined'?WebGLRenderingContext.prototype:null);` +
    `p(typeof WebGL2RenderingContext!=='undefined'?WebGL2RenderingContext.prototype:null);})();`

  const NativeWorker = Worker
  function StealthWorker(scriptURL, options) {
    if (typeof scriptURL === 'string' && scriptURL.startsWith('blob:')) {
      try {
        const xhr = new XMLHttpRequest()
        xhr.open('GET', scriptURL, false)
        xhr.send(null)
        const blob = new Blob([workerPatch + xhr.responseText], {
          type: 'application/javascript'
        })
        scriptURL = URL.createObjectURL(blob)
      } catch (_) {}
    }
    return new NativeWorker(scriptURL, options)
  }

  utils.replaceProperty(globalThis, 'Worker', { value: StealthWorker })
  utils.patchToString(StealthWorker, 'function Worker() { [native code] }')
}