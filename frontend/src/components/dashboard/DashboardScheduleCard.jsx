import {
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";

import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import AddRoundedIcon from "@mui/icons-material/AddRounded";

import { TYPOGRAPHY } from "../../theme/typography";

export default function DashboardScheduleCard({ schedule = [], onCreatePost }) {
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
              {schedule.length} posts planned for today
            </Typography>
          </Box>

          {/* Right */}
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            sx={{
              color: "#64748B",
              flexShrink: 0,
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

        {/* Empty State */}

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
      </CardContent>
    </Card>
  );
}
