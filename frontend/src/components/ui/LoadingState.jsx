import { useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Box, Typography } from "@mui/material";
import LoadingSpinner from "./LoadingSpinner";

const SCROLL_CLIP_VALUES = new Set(["auto", "scroll", "hidden", "clip"]);

const variantSx = {
  page: {
    width: "100%",
    minHeight: "calc(100dvh - 144px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  viewport: {
    position: "fixed",
    inset: 0,
    zIndex: 1400,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  container: {
    width: "100%",
    minHeight: 120,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    px: 2,
    py: 2,
  },
  overlay: {
    position: "fixed",
    zIndex: 10,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "linear-gradient(145deg, rgba(240,246,255,.74), rgba(255,255,255,.78))",
    backdropFilter: "blur(5px)",
    pointerEvents: "none",
  },
  inline: {
    width: "fit-content",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
};

function getVisibleBounds(anchor) {
  const container = anchor?.parentElement;
  if (!container) return null;

  const containerRect = container.getBoundingClientRect();
  let left = Math.max(0, containerRect.left);
  let top = Math.max(0, containerRect.top);
  let right = Math.min(window.innerWidth, containerRect.right);
  let bottom = Math.min(window.innerHeight, containerRect.bottom);

  for (let ancestor = container.parentElement; ancestor && ancestor !== document.body; ancestor = ancestor.parentElement) {
    const style = window.getComputedStyle(ancestor);
    const rect = ancestor.getBoundingClientRect();

    if (SCROLL_CLIP_VALUES.has(style.overflowX)) {
      left = Math.max(left, rect.left);
      right = Math.min(right, rect.right);
    }

    if (SCROLL_CLIP_VALUES.has(style.overflowY)) {
      top = Math.max(top, rect.top);
      bottom = Math.min(bottom, rect.bottom);
    }
  }

  if (right <= left || bottom <= top) return null;
  return { left, top, width: right - left, height: bottom - top };
}

function LoadingIndicator({ loadingLabel, variant, minHeight, sx = {} }) {
  return (
    <Box
      role="status"
      aria-live="polite"
      aria-atomic="true"
      aria-busy="true"
      aria-label={loadingLabel}
      sx={{
        ...(variantSx[variant] || variantSx.page),
        ...(minHeight !== undefined ? { minHeight } : {}),
        ...sx,
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: variant === "inline" ? "row" : "column",
          alignItems: "center",
          gap: variant === "inline" ? 1 : 1.15,
          px: 1,
        }}
      >
        <LoadingSpinner size={variant === "inline" ? 18 : 28} decorative />
        <Typography
          component="p"
          sx={{
            color: "#8995A9",
            fontSize: { xs: 11, sm: 12 },
            lineHeight: 1.4,
            fontWeight: 700,
            letterSpacing: "0.16em",
            textAlign: "center",
            textTransform: "uppercase",
          }}
        >
          {loadingLabel}
        </Typography>

      </Box>
    </Box>
  );
}

export default function LoadingState({
  page,
  label,
  message,
  variant = "page",
  minHeight,
  sx = {},
}) {
  const loadingLabel = label
    || message
    || (page ? `LOADING ${String(page).toUpperCase()}...` : "Loading...");
  const anchorRef = useRef(null);
  const [visibleBounds, setVisibleBounds] = useState(null);

  useLayoutEffect(() => {
    if (variant !== "overlay") return undefined;

    const anchor = anchorRef.current;
    const container = anchor?.parentElement;
    if (!container) return undefined;

    const updateBounds = () => setVisibleBounds(getVisibleBounds(anchor));
    updateBounds();

    window.addEventListener("scroll", updateBounds, true);
    window.addEventListener("resize", updateBounds);

    const resizeObserver = typeof ResizeObserver === "undefined"
      ? null
      : new ResizeObserver(updateBounds);
    if (resizeObserver) {
      resizeObserver.observe(container);
      for (let ancestor = container.parentElement; ancestor && ancestor !== document.body; ancestor = ancestor.parentElement) {
        resizeObserver.observe(ancestor);
      }
    }

    return () => {
      window.removeEventListener("scroll", updateBounds, true);
      window.removeEventListener("resize", updateBounds);
      resizeObserver?.disconnect();
    };
  }, [variant]);

  if (variant === "overlay") {
    return (
      <>
        <Box ref={anchorRef} aria-hidden="true" sx={{ display: "none" }} />
        {visibleBounds && createPortal(
          <LoadingIndicator
            loadingLabel={loadingLabel}
            variant={variant}
            minHeight={minHeight}
            sx={{
              ...sx,
              top: visibleBounds.top,
              left: visibleBounds.left,
              width: visibleBounds.width,
              height: visibleBounds.height,
            }}
          />,
          document.body,
        )}
      </>
    );
  }

  return (
    <LoadingIndicator
      loadingLabel={loadingLabel}
      variant={variant}
      minHeight={minHeight}
      sx={sx}
    />
  );
}
