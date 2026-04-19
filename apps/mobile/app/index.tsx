/**
 * app/index.tsx
 * Entry redirect — onboarding first, then goal setup.
 */

import { Redirect } from "expo-router";
import React from "react";

export default function Index(): React.JSX.Element {
  return <Redirect href="/onboarding" />;
}
