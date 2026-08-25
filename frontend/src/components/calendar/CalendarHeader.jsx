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
          startIcon={<AddRoundedIcon />}
          onClick={handleCreatePost}
        >
          Create Post
        </PrimaryButton>
      </Box>
    </Stack>
  );
}