/**
 * app/+html.tsx
 * The HTML document Expo Router wraps every web page in.
 *
 * Without this file the export uses Expo's default document, which is fine for
 * a web page and wrong for something that should feel like an app on a phone:
 *
 *   viewport-fit=cover   content can sit under the notch instead of beside it
 *   theme-color          the browser chrome stays light and breaks the dark UI
 *   *-web-app-capable    "Add to Home Screen" opens a tab, not an app
 *   overscroll-behavior  the page rubber-bands on scroll — the single most
 *                        obvious tell that this is a website
 *   100dvh               Safari's address bar no longer eats the bottom row
 *
 * Deliberately NOT set: maximum-scale / user-scalable=no. It would make the
 * app feel more native and would also stop anyone from zooming in on their
 * own financial figures.
 */

import { ScrollViewStyleReset } from "expo-router/html";
import React from "react";

export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, viewport-fit=cover"
        />

        <title>FinSight.ai — know your runway</title>
        <meta
          name="description"
          content="How many months can you live on what you have? A deterministic engine
                   computes your runway; the AI only explains what it computed."
        />

        <meta name="theme-color" content="#131313" />
        <meta name="color-scheme" content="dark" />

        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="FinSight" />
        <meta name="format-detection" content="telephone=no" />

        {/* Keeps react-native-web ScrollViews scrolling natively on web. */}
        <ScrollViewStyleReset />

        <style dangerouslySetInnerHTML={{ __html: RESET }} />
      </head>
      <body>{children}</body>
    </html>
  );
}

const RESET = `
html, body, #root {
  height: 100%;
  background-color: #131313;
}

/* Dynamic viewport height: the static 100vh includes the space Safari's
   address bar occupies, so the bottom of the screen is cut off until the
   user scrolls. */
@supports (height: 100dvh) {
  html, body, #root { height: 100dvh; }
}

body {
  margin: 0;
  overscroll-behavior-y: none;      /* no rubber-band bounce */
  -webkit-text-size-adjust: 100%;   /* no font inflation in landscape */
  -webkit-tap-highlight-color: transparent;
}

/* The frame in _layout.tsx paints the app column; this paints everything
   around it on a wide screen. */
#root { display: flex; flex-direction: column; }

input, textarea, select { font-family: inherit; }
`;
