import {
  Box,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { alpha } from "@mui/material/styles";

import BusinessRoundedIcon from "@mui/icons-material/BusinessRounded";

import { TYPOGRAPHY } from "../../../theme/typography";
import { getStatusMeta } from "./statusMeta";
import { getPlatformMeta } from "./platformMeta";
import CalendarEventStatusTrack from "./CalendarEventStatusTrack";

export default function CalendarEventDetailsHeader({
  event,
}) {
  if (!event) {
    return null;
  }

  const statusMeta = getStatusMeta(event.status);
  const StatusIcon = statusMeta.icon;

  const platformMeta = getPlatformMeta(event.platform);
  const PlatformIcon = platformMeta?.icon;
  const platformColor = platformMeta?.color;

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        mt: 2.5,
      }}
    >
      {/* ==========================================
          STATUS + PLATFORM
      ========================================== */}

      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        flexWrap="wrap"
        useFlexGap
      >
        {event.status && (
          <Chip
            icon={
              <StatusIcon
                sx={{
                  fontSize: "16px !important",
                  color: `${statusMeta.palette} !important`,
                }}
              />
            }
            label={statusMeta.label}
            size="small"
            sx={{
              height: 28,
              px: 0.25,
              borderRadius: 1.5,
              bgcolor: "action.hover",
              color: statusMeta.palette,
              ...TYPOGRAPHY.caption,
              fontWeight: 700,
              "& .MuiChip-label": {
                px: 0.75,
              },
            }}
          />
        )}

        {platformMeta && (
          <Box
            sx={{
              height: 28,
              display: "flex",
              alignItems: "center",
              gap: 0.75,
              pl: 0.75,
              pr: 1.25,
              borderRadius: 1.5,
              bgcolor: platformColor
                ? (theme) =>
                    alpha(platformColor, 0.1)
                : "action.hover",
              color: platformColor || "text.secondary",
            }}
          >
            <Box
              sx={{
                width: 20,
                height: 20,
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                bgcolor: platformColor || "action.hover",
                flexShrink: 0,
              }}
            >
              <PlatformIcon
                sx={{
                  fontSize: 12,
                  color: platformColor
                    ? "#fff"
                    : "text.secondary",
                }}
              />
            </Box>

            <Typography
              sx={{
                ...TYPOGRAPHY.caption,
                fontWeight: 700,
                color: platformColor || "text.secondary",
                letterSpacing: "0.01em",
              }}
            >
              {platformMeta.label}
            </Typography>
          </Box>
        )}
      </Stack>

      {/* ==========================================
          TITLE
      ========================================== */}

      <Typography
        component="h2"
        sx={{
          ...TYPOGRAPHY.sectionTitle,
          mt: 1.5,
          color: "text.primary",
          fontSize: { xs: "20px", sm: "22px" },
          lineHeight: { xs: "27px", sm: "29px" },
          fontWeight: 700,
          letterSpacing: "-0.015em",
          wordBreak: "break-word",
        }}
      >
        {event.title || "Untitled post"}
      </Typography>

      {/* ==========================================
          ORGANIZATION
      ========================================== */}

      {event.organization?.name && (
        <Stack
          direction="row"
          alignItems="center"
          spacing={0.75}
          sx={{ mt: 1 }}
        >
          <BusinessRoundedIcon
            sx={{
              fontSize: 16,
              color: "text.secondary",
              flexShrink: 0,
            }}
          />

          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,
              color: "text.secondary",
              fontWeight: 500,
              lineHeight: "20px",
            }}
          >
            {event.organization.name}
          </Typography>
        </Stack>
      )}

      {/* ==========================================
          LIFECYCLE TRACK
      ========================================== */}

      <Box sx={{ mt: 2.5, px: 0.5 }}>
        <CalendarEventStatusTrack
          status={event.status}
        />
      </Box>
    </Box>
  );
}