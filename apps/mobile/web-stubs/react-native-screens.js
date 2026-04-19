/**
 * web-stubs/react-native-screens.js
 * Web stub for react-native-screens — replaces native screen components
 * with plain React Native View equivalents so expo-router works on web.
 */
const React = require("react");
const { View, ScrollView } = require("react-native");

function enableScreens() {}
function screensEnabled() { return false; }

const Screen = View;
const ScreenContainer = View;
const NativeScreen = View;
const NativeScreenContainer = View;
const ScreenStack = View;
const ScreenStackHeaderConfig = View;
const ScreenStackHeaderSubview = View;
const FullWindowOverlay = View;
const SearchBar = View;

module.exports = {
  enableScreens,
  screensEnabled,
  Screen,
  ScreenContainer,
  NativeScreen,
  NativeScreenContainer,
  ScreenStack,
  ScreenStackHeaderConfig,
  ScreenStackHeaderSubview,
  FullWindowOverlay,
  SearchBar,
  // Native constants no-ops
  ScreensNativeModuleMock: {},
  TransitionPresets: {},
  // Default export
  default: { enableScreens, screensEnabled },
};
