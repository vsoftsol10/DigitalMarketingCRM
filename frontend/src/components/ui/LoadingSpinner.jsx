import { Box } from "@mui/material";

const sizeMap = {
  small: 16,
  medium: 24,
  large: 32,
};

export default function LoadingSpinner({
  size = "medium",
  color = "primary",
  thickness,
  ariaLabel = "Loading",
  decorative = false,
  sx = {},
}) {
  const diameter = typeof size === "number" ? size : sizeMap[size] || sizeMap.medium;
  const borderWidth = thickness || Math.max(2, Math.round(diameter / 8));

  return (
    <Box
      {...(decorative
        ? { "aria-hidden": true }
        : {
          role: "status",
          "aria-live": "polite",
          "aria-label": ariaLabel,
          "aria-busy": "true",
        })}
      sx={{
        display: "inline-block",
        flex: "0 0 auto",
        width: diameter,
        height: diameter,
        boxSizing: "border-box",
        border: `${borderWidth}px solid currentColor`,
        borderTopColor: "transparent",
        borderRadius: "50%",
        color: color === "inherit" ? "inherit" : "primary.main",
        animation: "dmcLoadingSpinner 0.8s linear infinite",
        "@keyframes dmcLoadingSpinner": {
          to: { transform: "rotate(360deg)" },
        },
        "@media (prefers-reduced-motion: reduce)": {
          animation: "none",
        },
        ...sx,
      }}
    />
  );
}
