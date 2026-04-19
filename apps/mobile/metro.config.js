const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const config = getDefaultConfig(__dirname);

config.resolver.sourceExts = [...config.resolver.sourceExts, "mjs", "cjs"];

// Production web: fix expo-font's registerWebModule crash.
//
// ROOT CAUSE: expo-font's ExpoFontLoader.web.ts passes `createExpoFontLoader`
// (a named function) to registerWebModule(). Terser's `inline` optimization
// replaces it with an anonymous arrow (() => ExpoFontLoader) whose .name is "",
// triggering "Module implementation must be a class" inside registerWebModule.
//
// FIX: disable function inlining + preserve all function/class names.
config.transformer.minifierConfig = {
  compress: {
    ecma: 2020,
    inline: false,          // ← THE FIX: don't inline named fns to anonymous
    keep_fnames: true,      // don't remove named function expressions
    keep_classnames: true,
  },
  mangle: {
    keep_fnames: true,      // don't rename functions (preserves .name)
    keep_classnames: true,
  },
  output: { ecma: 2020 },
};

// On web: replace react-native-screens with a plain View stub
// to avoid "Module implementation must be a class" from expo-modules-core
const WEB_STUBS = {
  "react-native-screens": "web-stubs/react-native-screens.js",
  "react-native-safe-area-context": "web-stubs/react-native-safe-area-context.js",
};

config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === "web" && WEB_STUBS[moduleName]) {
    return {
      filePath: path.resolve(__dirname, WEB_STUBS[moduleName]),
      type: "sourceFile",
    };
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
