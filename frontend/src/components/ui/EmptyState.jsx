import { Box, Button, Paper, Stack, Typography } from "@mui/material";

/** Render only after a request succeeds with an empty result. */
export default function EmptyState({
  icon,
  title = "Nothing here yet",
  description = "There is nothing to show right now.",
  actionLabel,
  onAction,
  sx = {},
}) {
  return (
    <Box
      component="section"
      role="status"
      aria-label={title}
      sx={{
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: { xs: 1.5, sm: 2 },
        py: { xs: 2, sm: 3 },
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
          boxShadow: "0 12px 28px rgba(42, 61, 110, 0.06)",
        }}
      >
        <Stack spacing={1.5} alignItems="center">
          {icon && (
            <Box
              aria-hidden="true"
              sx={{
                width: 52,
                height: 52,
                display: "grid",
                placeItems: "center",
                borderRadius: "50%",
                color: "#5269B4",
                bgcolor: "#EFF4FF",
                "& svg": { fontSize: 27 },
              }}
            >
              {icon}
            </Box>
          )}
          <Typography
            component="h2"
            sx={{ color: "#1E293B", fontWeight: 700, fontSize: { xs: 18, sm: 20 } }}
          >
            {title}
          </Typography>
          {description && (
            <Typography
              sx={{
                maxWidth: 420,
                color: "#64748B",
                fontSize: 14,
                lineHeight: 1.65,
                overflowWrap: "anywhere",
              }}
            >
              {description}
            </Typography>
          )}
          {actionLabel && typeof onAction === "function" && (
            <Button
              variant="contained"
              onClick={onAction}
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
              {actionLabel}
            </Button>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}
