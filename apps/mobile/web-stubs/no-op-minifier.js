/**
 * web-stubs/no-op-minifier.js
 * Metro minifier that passes code through unchanged.
 *
 * WHY: expo-modules-core's registerWebModule() checks
 *   `implementation.prototype instanceof WebModule`
 * which breaks when Terser/Babel downgrades ES6 class syntax to ES5
 * functions in production builds.
 *
 * Disabling minification preserves class syntax so the check passes.
 * Trade-off: bundle is ~2-3× larger, but it's cached after first load.
 */
async function minify({ code, map }) {
  return { code, map: map || "" };
}

module.exports = minify;
