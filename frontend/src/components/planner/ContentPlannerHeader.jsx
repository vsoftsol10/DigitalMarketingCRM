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
            px: 2.8,
            borderRadius: "17px",
            border: "1px solid rgba(255,255,255,.7)",
            background:
              "linear-gradient(115deg, #A96BEA 0%, #7074ED 54%, #4A91ED 100%)",
            boxShadow:
              "0 11px 22px rgba(100,92,203,.3), 0 3px 7px rgba(65,101,210,.17), inset 0 1px 0 rgba(255,255,255,.46), inset 0 -2px 3px rgba(67,71,163,.16)",
            ...TYPOGRAPHY.formButton,

            "&:hover": {
              background:
                "linear-gradient(115deg, #9D60E3 0%, #5E70E8 56%, #3D8FEA 100%)",
              boxShadow:
                "0 13px 24px rgba(100,92,203,.34), 0 3px 8px rgba(65,101,210,.2), inset 0 1px 0 rgba(255,255,255,.42)",
            },

            "&:focus-visible": {
              outline: "3px solid rgba(109,139,218,.42)",
              outlineOffset: 3,
            },

            "&:active": {
              transform: "translateY(1px)",
              boxShadow:
                "0 6px 13px rgba(100,92,203,.24), inset 0 2px 4px rgba(67,71,163,.18)",
            },

            "&.Mui-disabled": {
              color: "rgba(255,255,255,.8)",
              background: "linear-gradient(115deg, #B995DD, #8E9BE0)",
              borderColor: "rgba(255,255,255,.58)",
              boxShadow: "0 4px 9px rgba(100,92,203,.12)",
            },
          }}
        >
          New Idea
        </Button>
      </Stack>
    </Box>
  );
}
