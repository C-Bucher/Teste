/**
 * Runs a loader right after the effect, outside its synchronous body.
 *
 * Loaders here flip a "loading" flag and then fill data; calling them inline in an effect makes
 * React re-render inside the effect (react-hooks/set-state-in-effect). Deferring to a microtask
 * keeps the same timing for the user while every setState happens after the effect returns.
 */
export const defer = (loader: () => unknown) => {
  queueMicrotask(() => {
    void loader();
  });
};
