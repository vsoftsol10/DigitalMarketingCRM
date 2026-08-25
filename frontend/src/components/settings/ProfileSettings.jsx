import {
  Paper,
  Box,
} from "@mui/material";

import ProfileForm from "./ProfileForm";

export default function ProfileSettings({
  profile,
  loading = false,
  error = null,
  onSubmit,
}) {
  return (
    <Paper
      elevation={0}
      sx={{
        width: "100%",

        border: "1px solid",

        borderColor: "divider",

        borderRadius: 3,

        bgcolor: "background.paper",

        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          px: {
            xs: 2.5,
            sm: 3,
            md: 3.5,
          },

          py: {
            xs: 2.5,
            sm: 3,
            md: 3.5,
          },
        }}
      >
        <ProfileForm
          profile={profile}
          loading={loading}
          error={error}
          onSubmit={onSubmit}
        />
      </Box>
    </Paper>
  );
}