/* eslint-disable */
import * as Router from 'expo-router';

export * from 'expo-router';

declare module 'expo-router' {
  export namespace ExpoRouter {
    export interface __routes<T extends string | object = string> {
      hrefInputParams: { pathname: Router.RelativePathString, params?: Router.UnknownInputParams } | { pathname: Router.ExternalPathString, params?: Router.UnknownInputParams } | { pathname: `/baseline`; params?: Router.UnknownInputParams; } | { pathname: `/decision`; params?: Router.UnknownInputParams; } | { pathname: `/goal`; params?: Router.UnknownInputParams; } | { pathname: `/`; params?: Router.UnknownInputParams; } | { pathname: `/input`; params?: Router.UnknownInputParams; } | { pathname: `/onboarding`; params?: Router.UnknownInputParams; } | { pathname: `/scenario`; params?: Router.UnknownInputParams; } | { pathname: `/_sitemap`; params?: Router.UnknownInputParams; };
      hrefOutputParams: { pathname: Router.RelativePathString, params?: Router.UnknownOutputParams } | { pathname: Router.ExternalPathString, params?: Router.UnknownOutputParams } | { pathname: `/baseline`; params?: Router.UnknownOutputParams; } | { pathname: `/decision`; params?: Router.UnknownOutputParams; } | { pathname: `/goal`; params?: Router.UnknownOutputParams; } | { pathname: `/`; params?: Router.UnknownOutputParams; } | { pathname: `/input`; params?: Router.UnknownOutputParams; } | { pathname: `/onboarding`; params?: Router.UnknownOutputParams; } | { pathname: `/scenario`; params?: Router.UnknownOutputParams; } | { pathname: `/_sitemap`; params?: Router.UnknownOutputParams; };
      href: Router.RelativePathString | Router.ExternalPathString | `/baseline${`?${string}` | `#${string}` | ''}` | `/decision${`?${string}` | `#${string}` | ''}` | `/goal${`?${string}` | `#${string}` | ''}` | `/${`?${string}` | `#${string}` | ''}` | `/input${`?${string}` | `#${string}` | ''}` | `/onboarding${`?${string}` | `#${string}` | ''}` | `/scenario${`?${string}` | `#${string}` | ''}` | `/_sitemap${`?${string}` | `#${string}` | ''}` | { pathname: Router.RelativePathString, params?: Router.UnknownInputParams } | { pathname: Router.ExternalPathString, params?: Router.UnknownInputParams } | { pathname: `/baseline`; params?: Router.UnknownInputParams; } | { pathname: `/decision`; params?: Router.UnknownInputParams; } | { pathname: `/goal`; params?: Router.UnknownInputParams; } | { pathname: `/`; params?: Router.UnknownInputParams; } | { pathname: `/input`; params?: Router.UnknownInputParams; } | { pathname: `/onboarding`; params?: Router.UnknownInputParams; } | { pathname: `/scenario`; params?: Router.UnknownInputParams; } | { pathname: `/_sitemap`; params?: Router.UnknownInputParams; };
    }
  }
}
