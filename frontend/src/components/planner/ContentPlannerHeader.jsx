import { Box, Button, Stack, Typography } from "@mui/material";

import AddRoundedIcon from "@mui/icons-material/AddRounded";

import { TYPOGRAPHY } from "../../theme/typography";
import { plannerPrimaryButtonSx } from "./plannerUiSx";

export default function ContentPlannerHeader({ onCreateIdea }) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        flexWrap: "wrap",
        gap: 2,
        mb: 4,
      }}
    >
      {/* Left */}

      <Box sx={{ minWidth: 0 }}>
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

      <Stack direction="row" spacing={2} sx={{ width: { xs: "100%", sm: "auto" } }}>
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
            px: 2.8,
            ...TYPOGRAPHY.formButton,
            ...plannerPrimaryButtonSx,
            width: { xs: "100%", sm: "auto" },
          }}
        >
          New Idea
        </Button>
      </Stack>
    </Box>
  );
}
