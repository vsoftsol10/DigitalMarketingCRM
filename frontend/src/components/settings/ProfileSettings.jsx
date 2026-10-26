import {
  Paper,
  Box,
} from "@mui/material";

import ProfileForm from "./ProfileForm";
import { settingsGlassCardSx } from "./settingsGlassSx";

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
        ...settingsGlassCardSx,
        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          width: "100%",
          boxSizing: "border-box",
          py: {
            xs: 2.5,
            sm: 3,
            md: 3.5,
          },
          px: { xs: 2, sm: 3.25, md: 4 },
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
