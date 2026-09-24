import {
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";

import { TYPOGRAPHY } from "../../theme/typography";

const PLATFORM_CONFIG = {
  INSTAGRAM: { icon: InstagramIcon, color: "#E1306C", background: "#FDF2F8" },
  FACEBOOK: { icon: FacebookRoundedIcon, color: "#1877F2", background: "#EFF6FF" },
  LINKEDIN: { icon: LinkedInIcon, color: "#0A66C2", background: "#EFF6FF" },
  YOUTUBE: { icon: YouTubeIcon, color: "#FF0000", background: "#FEF2F2" },
};

function formatScheduledTime(scheduledAt, timezone) {
  if (!scheduledAt) {
    return "";
  }

  try {
    return new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
      timeZone: timezone || undefined,
    }).format(new Date(scheduledAt));
  } catch {
    return new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(scheduledAt));
  }
}

function getPlatformConfig(platform) {
  return PLATFORM_CONFIG[String(platform || "").toUpperCase()] || {
    icon: CalendarTodayOutlinedIcon,
    color: "#64748B",
    background: "#F1F5F9",
  };
}

export default function DashboardScheduleCard({ schedule = [], onCreatePost }) {
  const navigate = useNavigate();
  const scheduleItems = Array.isArray(schedule) ? schedule : [];

  function openCalendarTarget(targetId) {
    navigate("/calendar", {
      state: {
        targetId,
      },
    });
  }

  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "22px",
        height: 520,
      }}
    >
      <CardContent
        sx={{
          p: 4,
          height: "100%",
          display: "flex",
          flexDirection: "column",

          "&:last-child": {
            pb: 4,
          },
        }}
      >
        {/* Header */}

        <Stack
          direction="row"
          alignItems="flex-start"
          sx={{
            width: "100%",
          }}
        >
          {/* Left */}
          <Box sx={{ flex: 1 }}>
            <Typography sx={TYPOGRAPHY.sectionTitle}>
              Today's Schedule
            </Typography>

            <Typography
              sx={{
                mt: 0.5,
                fontSize: 15,
                color: "#64748B",
              }}
            >
              {scheduleItems.length} posts planned for today
            </Typography>
          </Box>

          {/* Right */}
          <Stack
            component="button"
            type="button"
            onClick={() => navigate("/calendar")}
            direction="row"
            spacing={1}
            alignItems="center"
            sx={{
              color: "#64748B",
              flexShrink: 0,
              border: 0,
              bgcolor: "transparent",
              p: 0,
              cursor: "pointer",
            }}
          >
            <CalendarTodayOutlinedIcon
              sx={{
                fontSize: 20,
              }}
            />

            <Typography
              sx={{
                fontSize: 15,
                fontWeight: 500,
              }}
            >
              Calendar
            </Typography>
          </Stack>
        </Stack>

        {scheduleItems.length === 0 ? (
          <Box
          sx={{
            flex: 1,

            display: "flex",
            flexDirection: "column",

            justifyContent: "center",
            alignItems: "center",

            textAlign: "center",
          }}
        >
          <Box
            sx={{
              width: 56,
              height: 56,

              borderRadius: "50%",

              bgcolor: "#F1F5F9",

              display: "flex",
              justifyContent: "center",
              alignItems: "center",

              mb: 4,
            }}
          >
            <CalendarTodayOutlinedIcon
              sx={{
                fontSize: 28,
                color: "#94A3B8",
              }}
            />
          </Box>

          <Typography
            sx={{
              fontSize: 18,
              fontWeight: 700,
              color: "#1E293B",
            }}
          >
            Nothing scheduled today
          </Typography>

          <Typography
            sx={{
              mt: 1,
              maxWidth: 360,

              fontSize: 16,

              lineHeight: 1.6,

              color: "#64748B",
            }}
          >
            Your calendar is clear. Create a post to fill today's schedule.
          </Typography>

          <Button
            variant="contained"
            startIcon={<AddRoundedIcon />}
            onClick={onCreatePost}
            sx={{
              mt: 4,

              height: 42,

              px: 3,

              borderRadius: "999px",

              textTransform: "none",

              fontSize: 15,
              fontWeight: 600,

              boxShadow: "none",

              "&:hover": {
                boxShadow: "none",
              },
            }}
          >
            Create Post
          </Button>
          </Box>
        ) : (
          <Box
            sx={{
              flex: 1,
              mt: 3,
              overflowY: "auto",
              pr: 0.5,

              "&::-webkit-scrollbar": {
                width: 4,
              },

              "&::-webkit-scrollbar-thumb": {
                background: "#CBD5E1",
                borderRadius: 20,
              },
            }}
          >
            {scheduleItems.map((item, index) => (
              <Box
                key={item.target_id}
                component="button"
                type="button"
                onClick={() => openCalendarTarget(item.target_id)}
                aria-label={`Open ${item.title || "scheduled post"} in Calendar`}
                sx={{
                  width: "100%",
                  border: 0,
                  bgcolor: "transparent",
                  m: 0,
                  p: 1.5,
                  textAlign: "left",
                  font: "inherit",
                  cursor: "pointer",
                  borderRadius: "14px",
                  borderBottom:
                    index === scheduleItems.length - 1
                      ? "none"
                      : "1px solid #E2E8F0",
                  transition: "background-color 0.2s ease, border-color 0.2s ease",
                  "&:hover": {
                    bgcolor: "#F8FAFC",
                  },
                  "&:focus-visible": {
                    outline: "2px solid #2563EB",
                    outlineOffset: "2px",
                  },
                }}
              >
                {(() => {
                  const platformConfig = getPlatformConfig(item.platform);
                  const PlatformIcon = platformConfig.icon;

                  return (
                    <Stack direction="row" spacing={1.5} alignItems="center">
                      <Box
                        sx={{
                          width: 38,
                          height: 38,
                          borderRadius: "12px",
                          bgcolor: platformConfig.background,
                          color: platformConfig.color,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          flexShrink: 0,
                        }}
                      >
                        <PlatformIcon sx={{ fontSize: 20 }} />
                      </Box>

                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Stack direction="row" justifyContent="space-between" spacing={1}>
                          <Typography sx={{ fontSize: 14, fontWeight: 700, color: "#1E293B" }}>
                            {formatScheduledTime(item.scheduled_at, item.timezone)}
                          </Typography>
                          <Typography sx={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "capitalize" }}>
                            {item.platform?.toLowerCase() || ""}
                          </Typography>
                        </Stack>
                        <Typography noWrap title={item.title || "Untitled Post"} sx={{ mt: 0.35, fontSize: 15, fontWeight: 600, color: "#1E293B" }}>
                          {item.title || "Untitled Post"}
                        </Typography>
                        <Typography noWrap title={`${item.organization_name || ""}${item.social_account ? ` • ${item.social_account}` : ""}`} sx={{ mt: 0.2, fontSize: 13, color: "#64748B" }}>
                          {item.organization_name}
                          {item.social_account ? ` • ${item.social_account}` : ""}
                        </Typography>
                      </Box>

                      <ArrowForwardRoundedIcon sx={{ color: "#94A3B8", fontSize: 20, flexShrink: 0 }} />
                    </Stack>
                  );
                })()}
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
