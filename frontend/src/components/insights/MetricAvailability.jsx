import { Box, Typography } from "@mui/material";

const STATUS_LABELS = {
  permission_required: "Permission required",
  not_supported: "Not supported",
  unavailable: "Unavailable",
  provider_error: "Provider error",
};

function availabilityLabel(status) {
  return STATUS_LABELS[status] || "Unavailable";
}

function formatReason(reason) {
  if (!reason) return "";
  return String(reason).replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

export default function MetricAvailability({
  status,
  reason,
  emptyText = "Select an account",
  compact = false,
}) {
  const label = status ? availabilityLabel(status) : emptyText;
  const detail = status ? formatReason(reason) : "";

  return (
    <Box sx={{ minWidth: 0 }}>
      <Typography
        component="span"
        sx={{
          display: "inline-block",
          color: status === "provider_error" ? "error.main" : "text.secondary",
          fontSize: compact ? 12 : 13,
          fontWeight: 500,
          lineHeight: 1.4,
          textTransform: "capitalize",
        }}
      >
        {label}
      </Typography>
      {detail && (
        <Typography
          component="span"
          sx={{ display: "block", mt: 0.25, color: "text.secondary", fontSize: 11 }}
        >
          {detail}
        </Typography>
      )}
    </Box>
  );
}
