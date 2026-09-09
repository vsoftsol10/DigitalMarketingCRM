import { Avatar, Box, Stack, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../../../theme/typography";

// ============================================================
// COMPONENT
// ============================================================

export default function PreviewHeader({
  organization,
  platform,
  accounts = [],
}) {
  // ==========================================================
  // ACCOUNT LABELS
  // ==========================================================

  const accountLabels = Array.isArray(accounts)
    ? accounts
        .map(
          (account) =>
            account?.username ||
            account?.accountName ||
            account?.pageName ||
            account?.name ||
            "",
        )
        .filter(Boolean)
    : [];

  const uniqueAccountLabels = [...new Set(accountLabels)];

  const accountText =
    uniqueAccountLabels.length > 0 ? uniqueAccountLabels.join(" • ") : "";

  // ==========================================================
  // ORGANIZATION AVATAR
  // ==========================================================

  const organizationInitial =
    organization?.name?.trim()?.charAt(0)?.toUpperCase() || "O";

  // ==========================================================
  // PLATFORM TEXT
  // ==========================================================

  const platformName = platform?.name || "Social account";

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Stack
      direction="row"
      spacing={1.5}
      alignItems="center"
      sx={{
        p: 2,
      }}
    >
      {/* ====================================================
          ORGANIZATION AVATAR
      ==================================================== */}

      <Avatar
        sx={{
          width: 42,
          height: 42,

          bgcolor: "#2563EB",

          fontSize: 16,
          fontWeight: 600,
        }}
      >
        {organizationInitial}
      </Avatar>

      {/* ====================================================
          INFORMATION
      ==================================================== */}

      <Box
        sx={{
          flex: 1,

          minWidth: 0,
        }}
      >
        {/* ==================================================
            ORGANIZATION
        ================================================== */}

        <Typography
          sx={{
            ...TYPOGRAPHY.body,

            fontWeight: 600,

            color: "#0F172A",

            overflow: "hidden",

            textOverflow: "ellipsis",

            whiteSpace: "nowrap",
          }}
        >
          {organization?.name || "Organization"}
        </Typography>

        {/* ==================================================
            ACCOUNT / PLATFORM
        ================================================== */}

        <Typography
          sx={{
            ...TYPOGRAPHY.caption,

            overflow: "hidden",

            textOverflow: "ellipsis",

            whiteSpace: "nowrap",
          }}
        >
          {accountText
            ? `${accountText} • ${platformName}`
            : `${platformName} • Just now`}
        </Typography>
      </Box>
    </Stack>
  );
}
