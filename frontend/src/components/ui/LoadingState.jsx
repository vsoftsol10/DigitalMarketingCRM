import { useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Box, Typography } from "@mui/material";

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
          flexDirection: "column",
          alignItems: "center",
          gap: 1.15,
          px: 1,
        }}
      >
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

        <Box
          aria-hidden="true"
          sx={{
            position: "relative",
            width: { xs: 128, sm: 140 },
            height: 4,
            overflow: "hidden",
            borderRadius: 99,
            background: "rgba(130,148,177,.16)",
            "&::before": {
              content: '""',
              position: "absolute",
              inset: "0 auto 0 0",
              width: "28%",
              borderRadius: 99,
              background: "linear-gradient(90deg, #A96BEA 0%, #7074ED 52%, #4A91ED 100%)",
              boxShadow: "0 0 8px rgba(112,116,237,.22)",
              animation: "loadingLineSlide 1.35s ease-in-out infinite",
            },
            "@keyframes loadingLineSlide": {
              "0%": { transform: "translateX(-110%)" },
              "100%": { transform: "translateX(470%)" },
            },
          }}
        />
      </Box>
    </Box>
  );
}

export default function LoadingState({
  page,
  label,
  variant = "page",
  minHeight,
  sx = {},
}) {
  const loadingLabel = label || `LOADING ${String(page || "").toUpperCase()}...`;
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
