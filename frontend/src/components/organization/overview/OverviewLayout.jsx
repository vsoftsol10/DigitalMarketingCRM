import { Box } from "@mui/material";

export default function OverviewLayout({
  brandInformation,
  contactInformation,
  socialAccounts,
  activityTimeline,

  profile,
  subscription,
}) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: { xs: "column", lg: "row" },
        gap: 3,
        alignItems: "flex-start",
      }}
    >
      {/* Left */}

      <Box
        sx={{
          flex: 1,
          minWidth: 0,

          display: "flex",
          flexDirection: "column",

          gap: 3,
        }}
      >
        {brandInformation}

        {contactInformation}

        {socialAccounts}

        {activityTimeline}
      </Box>

      {/* Right */}

      <Box
        sx={{
          width: { xs: "100%", lg: 360 },

          flexShrink: 0,

          display: "flex",
          flexDirection: "column",

          gap: 3,

          position: { xs: "static", lg: "sticky" },
          top: { lg: 24 },
        }}
      >
        {profile}

        {subscription}
      </Box>
    </Box>
  );
}
