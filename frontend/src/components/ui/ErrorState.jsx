import { useId } from "react";
import { Box, Button, Paper, Stack, Typography } from "@mui/material";
import ErrorOutlineRoundedIcon from "@mui/icons-material/ErrorOutlineRounded";
import RefreshRoundedIcon from "@mui/icons-material/RefreshRounded";

import { formatApiErrorMessage } from "../../utils/apiErrorMessage";

const variantSx = {
  page: {
    minHeight: "calc(100dvh - 144px)",
  },
  container: {
    minHeight: 240,
  },
  inline: {
    minHeight: 0,
    py: 2,
  },
};

export default function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  retryLabel = "Try again",
  variant = "container",
  sx = {},
}) {
  const id = useId();
  const displayMessage = formatApiErrorMessage(message, {
    fallback: "We couldn't complete this request. Please try again.",
  });

  return (
    <Box
      component="section"
      role="alert"
      aria-labelledby={`${id}-title`}
      aria-describedby={`${id}-description`}
      sx={{
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: { xs: 1.5, sm: 2 },
        py: { xs: 2, sm: 3 },
        ...variantSx[variant],
        ...sx,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: "100%",
          maxWidth: 520,
          p: { xs: 2.5, sm: 3.5 },
          border: "1px solid #E2E8F0",
          borderRadius: { xs: 3, sm: 4 },
          bgcolor: "#FFFFFF",
          textAlign: "center",
          boxShadow: "0 12px 28px rgba(42, 61, 110, 0.08)",
        }}
      >
        <Stack spacing={1.5} alignItems="center">
          <Box
            aria-hidden="true"
            sx={{
              width: 52,
              height: 52,
              display: "grid",
              placeItems: "center",
              borderRadius: "50%",
              color: "#B42318",
              bgcolor: "#FEF3F2",
            }}
          >
            <ErrorOutlineRoundedIcon sx={{ fontSize: 28 }} />
          </Box>
          <Typography
            id={`${id}-title`}
            component="h2"
            sx={{ color: "#1E293B", fontWeight: 700, fontSize: { xs: 18, sm: 20 } }}
          >
            {title}
          </Typography>
          <Typography
            id={`${id}-description`}
            sx={{
              maxWidth: 420,
              color: "#64748B",
              fontSize: 14,
              lineHeight: 1.65,
              overflowWrap: "anywhere",
            }}
          >
            {displayMessage}
          </Typography>
          {typeof onRetry === "function" && (
            <Button
              variant="contained"
              startIcon={<RefreshRoundedIcon />}
              onClick={onRetry}
              sx={{
                mt: 0.5,
                minHeight: 42,
                px: 2.5,
                borderRadius: 2,
                bgcolor: "#2563EB",
                fontWeight: 600,
                textTransform: "none",
                "&:hover": { bgcolor: "#1D4ED8" },
              }}
            >
              {retryLabel}
            </Button>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}
