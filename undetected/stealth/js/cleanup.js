// Drop injector globals after evasions are applied.

() => {
  try {
    delete globalThis.utils
  } catch (_) {}
}