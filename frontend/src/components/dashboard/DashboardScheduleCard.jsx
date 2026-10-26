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
        position: "relative",
        overflow: "hidden",
        border: "1px solid rgba(255,255,255,.9)",
        borderRadius: "24px",
        height: { xs: 440, lg: 390 },
        background: "linear-gradient(145deg, rgba(250,252,255,.98) 0%, rgba(242,247,255,.96) 58%, rgba(237,244,255,.92) 100%)",
        boxShadow: "0 16px 30px rgba(75,96,151,.14), 0 3px 8px rgba(79,99,154,.09), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -2px 5px rgba(112,127,177,.08)",
        backdropFilter: "blur(16px)",
        "&::before": {
          content: "\"\"",
          position: "absolute",
          inset: 4,
          borderRadius: "20px",
          border: "1px solid rgba(255,255,255,.78)",
          pointerEvents: "none",
        },
      }}
    >
      <CardContent
        sx={{
          position: "relative",
          zIndex: 1,
          p: { xs: 2.5, md: 3 },
          height: "100%",
          display: "flex",
          flexDirection: "column",

          "&:last-child": {
            pb: { xs: 2.5, md: 3 },
          },
        }}
      >
        {/* Header */}

        <Stack
          direction="row"
          sx={{
            width: "100%",
            alignItems: "center",
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
              borderRadius: "999px",
          background: "linear-gradient(145deg, rgba(247,250,255,.98), rgba(228,237,253,.94))",
          border: "1px solid rgba(255,255,255,.96)",
              px: 1.5,
              py: 1,
              cursor: "pointer",
              boxShadow: "0 6px 13px rgba(75,96,151,.12), inset 0 2px 2px rgba(255,255,255,.98), inset 0 -1px 2px rgba(94,111,159,.06)",
            }}
          >
            <CalendarTodayOutlinedIcon
              sx={{
                fontSize: 18,
                color: "#6F80A7",
              }}
            />

            <Typography
              sx={{
                fontSize: 14,
                fontWeight: 600,
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
              width: 78,
              height: 78,

              borderRadius: "50%",

              background: "linear-gradient(145deg, rgba(238,245,255,.98), rgba(222,234,252,.95))",
              border: "3px solid rgba(255,255,255,.96)",
              boxShadow: "0 10px 20px rgba(83,105,160,.18), 0 2px 5px rgba(76,97,150,.1), inset 0 2px 3px rgba(255,255,255,.98), inset 0 -3px 5px rgba(105,123,176,.12)",

              display: "flex",
              justifyContent: "center",
              alignItems: "center",

              mb: 2.2,
            }}
          >
            <CalendarTodayOutlinedIcon
              sx={{
                fontSize: 30,
                color: "#7184AD",
                filter: "drop-shadow(0 1px 1px rgba(56,76,125,.16))",
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
            variant="outlined"
            startIcon={<AddRoundedIcon />}
            onClick={onCreatePost}
            sx={{
              mt: 2,
              height: 36,
              px: 2,
              borderRadius: "999px",
              color: "#5D6FC5",
              borderColor: "rgba(93,111,197,.3)",
              bgcolor: "rgba(255,255,255,.72)",
              boxShadow: "0 4px 9px rgba(75,96,151,.08), inset 0 1px 1px rgba(255,255,255,.96)",
              "&:hover": { bgcolor: "rgba(255,255,255,.96)", borderColor: "rgba(93,111,197,.45)" },

              textTransform: "none",

              fontSize: 15,
              fontWeight: 600,
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
