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
          width: 360,

          flexShrink: 0,

          display: "flex",
          flexDirection: "column",

          gap: 3,

          position: "sticky",
          top: 24,
        }}
      >
        {profile}

        {subscription}
      </Box>
    </Box>
  );
}
