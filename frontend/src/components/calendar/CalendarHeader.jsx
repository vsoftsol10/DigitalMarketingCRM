import {
  Box,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";

import AddRoundedIcon from "@mui/icons-material/AddRounded";

import { useNavigate } from "react-router-dom";

import PrimaryButton from "../ui/button/PrimaryButton";

import { TYPOGRAPHY } from "../../theme/typography";

export default function CalendarHeader() {
  const theme = useTheme();
  const navigate = useNavigate();

  function handleCreatePost() {
    navigate("/posts");
  }

  return (
    <Stack
      direction={{
        xs: "column",
        sm: "row",
      }}
      alignItems={{
        xs: "flex-start",
        sm: "center",
      }}
      justifyContent="space-between"
      sx={{
        width: "100%",
        minWidth: 0,
        boxSizing: "border-box",
        gap: 2,
      }}
    >
      {/* LEFT CONTENT */}

      <Box
        sx={{
          minWidth: 0,
          flex: 1,
        }}
      >
        <Typography
          component="h1"
          sx={{
            ...TYPOGRAPHY.calendarTitle,
            color: theme.palette.text.primary,
          }}
        >
          Calendar
        </Typography>

        <Typography
          component="p"
          sx={{
            ...TYPOGRAPHY.calendarDescription,
            color: theme.palette.text.secondary,
            mt: 0.5,
          }}
        >
          View all scheduled and published content across organizations.
        </Typography>
      </Box>

      {/* RIGHT ACTION */}

      <Box
        sx={{
          flexShrink: 0,
        }}
      >
        <PrimaryButton
          fullWidth={false}
          height={50}
          sx={{
            minWidth: 190,
            borderRadius: 999,
            background: "linear-gradient(105deg, #A46AF5 0%, #5B83F4 58%, #35B5E8 100%)",
            boxShadow: "0 9px 20px rgba(91,116,228,0.28), inset 0 1px 0 rgba(255,255,255,0.45)",
            border: "1px solid rgba(255,255,255,0.74)",
            "&:hover": {
              background: "linear-gradient(105deg, #9658EB 0%, #4D75E9 58%, #27A9DD 100%)",
              boxShadow: "0 12px 24px rgba(91,116,228,0.34)",
            },
          }}
          startIcon={<AddRoundedIcon />}
          onClick={handleCreatePost}
        >
          Create Post
        </PrimaryButton>
      </Box>
    </Stack>
  );
}
