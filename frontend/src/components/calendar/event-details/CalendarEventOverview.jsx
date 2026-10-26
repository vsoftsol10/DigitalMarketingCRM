import { Box, Stack, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";

import BusinessRoundedIcon from "@mui/icons-material/BusinessRounded";
import AccountCircleRoundedIcon from "@mui/icons-material/AccountCircleRounded";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import TodayRoundedIcon from "@mui/icons-material/TodayRounded";

import dayjs from "dayjs";

import { TYPOGRAPHY } from "../../../theme/typography";

function formatDate(date) {
  if (!date) {
    return null;
  }

  const parsedDate = dayjs(date);

  if (!parsedDate.isValid()) {
    return date;
  }

  return parsedDate.format("MMM D, YYYY");
}

function OverviewCard({ icon, iconColor, label, value }) {
  if (!value) {
    return null;
  }

  return (
    <Box
      sx={{
        minWidth: 0,
        p: 1.5,
        borderRadius: 2,
        border: "1px solid",
        borderColor: "rgba(202,220,248,0.84)",
        background: "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(236,245,255,0.84))",
        boxShadow: "0 5px 12px rgba(70,106,172,0.09), inset 0 1px 0 #FFFFFF, inset 0 -1px 0 rgba(190,211,244,0.32)",
        transition: "border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease",
        "&:hover": {
          borderColor: "#AFC8F0",
          boxShadow: "0 8px 16px rgba(70,106,172,0.14), inset 0 1px 0 #FFFFFF",
          transform: "translateY(-1px)",
        },
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        spacing={0.75}
        sx={{ mb: 0.75 }}
      >
        <Box
          sx={{
            width: 22,
            height: 22,
            borderRadius: iconColor ? "50%" : 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: iconColor
              ? alpha(iconColor, 0.12)
              : "transparent",
            color: iconColor || "text.disabled",
          }}
        >
          {icon}
        </Box>

        <Typography
          sx={{
            ...TYPOGRAPHY.caption,
            color: "text.secondary",
            fontWeight: 600,
            textTransform: "uppercase",
            fontSize: "10.5px",
            letterSpacing: "0.04em",
          }}
        >
          {label}
        </Typography>
      </Stack>

      <Typography
        noWrap
        sx={{
          ...TYPOGRAPHY.bodySmall,
          color: "text.primary",
          fontWeight: 600,
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {value}
      </Typography>
    </Box>
  );
}

export default function CalendarEventOverview({
  event,
}) {
  if (!event) {
    return null;
  }

  const eventDate = formatDate(event.date);
  const connectedAccount =
    event.socialAccount?.name ||
    event.social_account?.name ||
    event.socialAccount?.username ||
    event.social_account?.username ||
    event.socialAccount?.platform_account_id ||
    event.social_account?.platform_account_id ||
    "";

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        mt: 2.5,
        pt: 2.5,
        borderTop: "1px solid",
        borderColor: "divider",
      }}
    >
      <Typography
        component="h3"
        sx={{
          ...TYPOGRAPHY.cardTitle,
          color: "text.primary",
          mb: 1.5,
        }}
      >
        Overview
      </Typography>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(2, minmax(0, 1fr))",
          },
          gap: 1.25,
        }}
      >
        <OverviewCard
          icon={
            <BusinessRoundedIcon sx={{ fontSize: 17 }} />
          }
          label="Organization"
          value={event.organization?.name}
        />

        <OverviewCard
          icon={
            <AccountCircleRoundedIcon sx={{ fontSize: 17 }} />
          }
          label="Connected Account"
          value={connectedAccount}
        />

        <OverviewCard
          icon={
            <TodayRoundedIcon sx={{ fontSize: 17 }} />
          }
          label="Date"
          value={eventDate}
        />

        <OverviewCard
          icon={
            <ScheduleRoundedIcon
              sx={{ fontSize: 17 }}
            />
          }
          label="Time"
          value={event.time}
        />

        <OverviewCard
          icon={
            <ScheduleRoundedIcon
              sx={{ fontSize: 17, opacity: 0.6 }}
            />
          }
          label="Timezone"
          value={event.timezone}
        />
      </Box>
    </Box>
  );
}
