import { Box, Button, Stack, Typography } from "@mui/material";

import CalendarMonthOutlinedIcon from "@mui/icons-material/CalendarMonthOutlined";
import AddRoundedIcon from "@mui/icons-material/AddRounded";

import { TYPOGRAPHY } from "../../theme/typography";

export default function ContentPlannerHeader({ onMonthlyPlan, onCreateIdea }) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        flexWrap: "wrap",
        gap: 2,
        mb: 5,
      }}
    >
      {/* Left */}

      <Box>
        <Typography sx={TYPOGRAPHY.pageTitle}>Content Planner</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 1,
          }}
        >
          Plan and organize social media content.
        </Typography>
      </Box>

      {/* Right */}

      <Stack direction="row" spacing={2}>
        {/* <Button
          variant="outlined"
          startIcon={<CalendarMonthOutlinedIcon />}
          onClick={onMonthlyPlan}
          sx={{
            height: 48,
            px: 3,

            borderRadius: "14px",

            ...TYPOGRAPHY.button,

            borderColor: "#CBD5E1",

            color: "#334155",

            bgcolor: "#FFFFFF",

            "&:hover": {
              borderColor: "#94A3B8",
              bgcolor: "#F8FAFC",
            },
          }}
        >
          Monthly Plan
        </Button> */}

        <Button
          variant="contained"
          startIcon={<AddRoundedIcon />}
          onClick={onCreateIdea}
          sx={{
            height: 48,
            px: 3,

            borderRadius: "14px",

            ...TYPOGRAPHY.button,

            bgcolor: "#2563EB",

            boxShadow: "none",

            "&:hover": {
              bgcolor: "#1D4ED8",
              boxShadow: "none",
            },
          }}
        >
          New Idea
        </Button>
      </Stack>
    </Box>
  );
}
