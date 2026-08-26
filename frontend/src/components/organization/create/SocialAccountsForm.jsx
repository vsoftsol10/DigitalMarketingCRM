import { Box } from "@mui/material";

import SocialAccountsSection from "../social/SocialAccountsSection";

// ============================================================
// SOCIAL ACCOUNTS FORM
// ============================================================
//
// Create Organization page wrapper.
//
// IMPORTANT:
//
// Social Accounts UI itself lives in:
//
// components/organization/social/SocialAccountsSection.jsx
//
// This file is intentionally kept as a thin wrapper so the
// Create Organization page can continue using:
//
// <SocialAccountsForm />
//
// without duplicating social-account UI.
//
// Organization does not exist at this stage, so there is no
// organizationId and no backend/social-account fetch.
//
// The actual social accounts can be connected after the
// organization is created.
// ============================================================

export default function SocialAccountsForm() {
  return (
    <Box
      sx={{
        width: "100%",
      }}
    >
      <SocialAccountsSection
        mode="create"
        organizationId={null}
        accounts={[]}
      />
    </Box>
  );
}