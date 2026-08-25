import { Box, Chip, Divider, Stack, Typography } from "@mui/material";

import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";

function formatPlan(value) {
  if (!value) {
    return "-";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function formatBillingCycle(value) {
  if (!value) {
    return "-";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function formatStatus(value) {
  if (!value) {
    return "-";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function formatDate(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getStatusStyles(status) {
  switch (status) {
    case "active":
      return {
        background: "#ECFDF3",
        color: "#059669",
        border: "#A7F3D0",
      };

    case "scheduled":
      return {
        background: "#EFF6FF",
        color: "#2563EB",
        border: "#BFDBFE",
      };

    case "expired":
      return {
        background: "#FEF2F2",
        color: "#DC2626",
        border: "#FECACA",
      };

    case "cancelled":
      return {
        background: "#F8FAFC",
        color: "#64748B",
        border: "#CBD5E1",
      };

    default:
      return {
        background: "#F8FAFC",
        color: "#64748B",
        border: "#CBD5E1",
      };
  }
}

export default function SubscriptionHistoryItem({
  subscription,
  isLast = false,
}) {
  if (!subscription) {
    return null;
  }

  const statusStyles = getStatusStyles(subscription.status);

  return (
    <Box>
      <Stack direction="row" spacing={2} alignItems="flex-start">
        <Box
          sx={{
            width: 42,
            height: 42,

            borderRadius: "12px",

            backgroundColor: "#F8FAFC",

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            flexShrink: 0,
          }}
        >
          <CalendarTodayOutlinedIcon
            sx={{
              fontSize: 19,
              color: "#64748B",
            }}
          />
        </Box>

        <Box
          sx={{
            flex: 1,
            minWidth: 0,
          }}
        >
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            justifyContent="space-between"
          >
            <Typography
              sx={{
                fontSize: 16,
                lineHeight: "22px",
                fontWeight: 700,
                color: "#0F172A",
              }}
            >
              {formatPlan(subscription.plan_name)}
            </Typography>

            <Chip
              size="small"
              label={formatStatus(subscription.status)}
              sx={{
                height: 26,

                borderRadius: "999px",

                backgroundColor: statusStyles.background,

                color: statusStyles.color,

                border: "1px solid",

                borderColor: statusStyles.border,

                fontSize: 12,
                fontWeight: 600,
              }}
            />
          </Stack>

          <Typography
            sx={{
              mt: 0.35,

              fontSize: 13,
              color: "#64748B",
            }}
          >
            {formatBillingCycle(subscription.billing_cycle)}
          </Typography>

          <Stack
            direction={{
              xs: "column",
              sm: "row",
            }}
            spacing={{
              xs: 0.75,
              sm: 2,
            }}
            sx={{
              mt: 1.5,
            }}
          >
            <Typography
              sx={{
                fontSize: 13,
                color: "#64748B",
              }}
            >
              {formatDate(subscription.start_date)}
            </Typography>

            <Typography
              sx={{
                fontSize: 13,
                color: "#94A3B8",
              }}
            >
              →
            </Typography>

            <Typography
              sx={{
                fontSize: 13,
                color: "#64748B",
              }}
            >
              {formatDate(subscription.expiry_date)}
            </Typography>
          </Stack>
        </Box>
      </Stack>

      {!isLast && (
        <Divider
          sx={{
            my: 2.5,
          }}
        />
      )}
    </Box>
  );
}
