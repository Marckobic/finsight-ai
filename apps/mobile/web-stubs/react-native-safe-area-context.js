/**
 * web-stubs/react-native-safe-area-context.js
 * Web stub for react-native-safe-area-context.
 * On web there are no OS-level safe area insets — returns zeros everywhere
 * and renders children directly, avoiding the registerWebModule crash.
 */
const React = require("react");
const { View } = require("react-native");

const defaultInsets = { top: 0, right: 0, bottom: 0, left: 0 };
const defaultFrame  = { x: 0, y: 0, width: 0, height: 0 };
const defaultMetrics = { insets: defaultInsets, frame: defaultFrame };

const SafeAreaInsetsContext = React.createContext(defaultInsets);
const SafeAreaFrameContext  = React.createContext(defaultFrame);

function SafeAreaProvider({ children, style }) {
  return React.createElement(
    SafeAreaFrameContext.Provider,
    { value: defaultFrame },
    React.createElement(
      SafeAreaInsetsContext.Provider,
      { value: defaultInsets },
      React.createElement(View, { style: [{ flex: 1 }, style] }, children)
    )
  );
}

function SafeAreaView({ children, style }) {
  return React.createElement(View, { style: [{ flex: 1 }, style] }, children);
}

function useSafeAreaInsets() {
  return defaultInsets;
}

function useSafeAreaFrame() {
  return defaultFrame;
}

function useSafeAreaProviderCompat() {
  return defaultMetrics;
}

function withSafeAreaInsets(Component) {
  return function WrappedComponent(props) {
    return React.createElement(Component, Object.assign({}, props, { insets: defaultInsets }));
  };
}

const initialWindowMetrics = defaultMetrics;

module.exports = {
  SafeAreaProvider,
  SafeAreaView,
  SafeAreaInsetsContext,
  SafeAreaFrameContext,
  useSafeAreaInsets,
  useSafeAreaFrame,
  useSafeAreaProviderCompat,
  withSafeAreaInsets,
  initialWindowMetrics,
  default: SafeAreaProvider,
};
