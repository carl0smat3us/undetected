// Mitigate Runtime.Enable CDP leak — never pass Error objects to native console APIs.

() => {
  utils.preloadCache()

  // Reading err.stack lets CDP Runtime.Enable detection increment stackLookupCount.
  const safeErrorText = (err) => {
    if (!err || typeof err !== 'object') {
      return String(err)
    }
    return typeof err.message === 'string' && err.message ? err.message : 'Error'
  }

  const mapArgs = (args) =>
    args.map((arg) => (arg instanceof Error ? safeErrorText(arg) : arg))

  const consoleHandler = {
    apply(target, thisArg, args) {
      return Reflect.apply(target, thisArg, mapArgs(args))
    }
  }

  for (const name of [
    'log',
    'debug',
    'info',
    'warn',
    'error',
    'trace',
    'dir',
    'dirxml',
    'assert'
  ]) {
    if (!globalThis.console || typeof console[name] !== 'function') {
      continue
    }
    try {
      utils.replaceWithProxy(console, name, consoleHandler)
    } catch (_) {}
  }

  const contextHandler = {
    apply(target, thisArg, args) {
      const ctx = Reflect.apply(target, thisArg, args)
      if (!ctx || typeof ctx !== 'object') {
        return ctx
      }
      for (const name of ['debug', 'log', 'info', 'warn', 'error', 'trace']) {
        if (typeof ctx[name] !== 'function') {
          continue
        }
        try {
          utils.replaceWithProxy(ctx, name, consoleHandler)
        } catch (_) {}
      }
      return ctx
    }
  }

  if (typeof console.context === 'function') {
    try {
      utils.replaceWithProxy(console, 'context', contextHandler)
    } catch (_) {}
  }
}