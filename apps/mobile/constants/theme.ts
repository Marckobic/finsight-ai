/**
 * constants/theme.ts
 * FinSight.ai — Dark Design System Tokens.
 *
 * Material You dark color scheme.
 * Primary (orange): #FF6B00 / #ffb693
 * Tertiary (green): #78dc77
 */

export const COLORS = {
  // Backgrounds
  BACKGROUND: "#131313",
  SURFACE: "#201f1f",
  SURFACE_HIGH: "#2a2a2a",
  SURFACE_HIGHEST: "#353534",
  SURFACE_LOW: "#1c1b1b",
  SURFACE_LOWEST: "#0e0e0e",
  SURFACE_BRIGHT: "#393939",

  // Orange accent
  ORANGE: "#FF6B00",          // primary-container / CTA
  PRIMARY: "#ffb693",         // primary / text accent
  PRIMARY_FIXED: "#ffdbcc",

  // Green positive
  TERTIARY: "#78dc77",        // positive delta
  TERTIARY_CONTAINER: "#4aad4e",

  // Text
  TEXT_ON_SURFACE: "#e5e2e1",
  TEXT_SECONDARY: "#c6c6c6",
  TEXT_MUTED: "#6b6b6b",
  TEXT_ON_ORANGE: "#561f00",
  TEXT_ON_SURFACE_VARIANT: "#e2bfb0",

  // State
  ERROR: "#ffb4ab",
  OUTLINE: "#a98a7d",
  OUTLINE_VARIANT: "#5a4136",

  // ── Legacy compat (keeps old imports working) ──
  SILVER: "#131313",
  BLACK: "#000000",
  WHITE: "#FFFFFF",
  CARD: "#201f1f",
  CARD_BORDER: "#353534",
  INPUT_BG: "#353534",
  INPUT_BORDER: "#5a4136",
  INPUT_FOCUS_BORDER: "#FF6B00",
  TEXT_PRIMARY: "#e5e2e1",
  TEXT_ON_CARD: "#e5e2e1",
  TEXT_MUTED_ON_CARD: "#c6c6c6",
  POSITIVE: "#78dc77",
  NEGATIVE: "#ffb4ab",
  DISABLED: "rgba(255,255,255,0.65)",   // was #555555 — much more readable on dark bg
  DISABLED_BG: "#353534",
} as const;

export const SPACING = {
  XS: 4,
  SM: 8,
  MD: 16,
  LG: 24,
  XL: 32,
  XXL: 48,
} as const;

export const RADIUS = {
  SM: 4,
  MD: 8,
  LG: 12,
  PILL: 100,
} as const;

export const FONT = {
  SIZE_XS: 10,
  SIZE_SM: 12,
  SIZE_MD: 15,
  SIZE_LG: 18,
  SIZE_XL: 24,
  SIZE_XXL: 36,
  WEIGHT_REGULAR: "400" as const,
  WEIGHT_MEDIUM: "500" as const,
  WEIGHT_SEMIBOLD: "600" as const,
  WEIGHT_BOLD: "700" as const,
  WEIGHT_EXTRABOLD: "800" as const,
} as const;
