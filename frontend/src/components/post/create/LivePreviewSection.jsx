// import { Box, Paper, Typography } from "@mui/material";

// import { useFormContext } from "react-hook-form";
// import { useEffect, useState } from "react";

// import { TYPOGRAPHY } from "../../../theme/typography";

// import PreviewPlatformTabs from "./preview/PreviewPlatformTabs";
// import PreviewPostCard from "./preview/PreviewPostCard";

// export default function LivePreviewSection({
//   organizations = [],
//   platforms = [],
// }) {
//   const { watch } = useFormContext();

//   // ============================================================
//   // FORM STATE
//   // ============================================================

//   const organizationId = watch("organization");

//   const selectedPlatforms = watch("platforms") || [];

//   const platformContentTypes = watch("platform_content_types") || {};

//   const caption = watch("caption") || "";

//   const media = watch("media") || [];

//   // ============================================================
//   // ORGANIZATION
//   // ============================================================

//   const organization = organizations.find((item) => item.id === organizationId);

//   // ============================================================
//   // ACTIVE PLATFORM
//   // ============================================================

//   const [activePlatform, setActivePlatform] = useState("");

//   // ============================================================
//   // KEEP ACTIVE PLATFORM VALID
//   // ============================================================

//   useEffect(() => {
//     if (!selectedPlatforms.length) {
//       setActivePlatform("");
//       return;
//     }

//     if (!selectedPlatforms.includes(activePlatform)) {
//       setActivePlatform(selectedPlatforms[0]);
//     }
//   }, [selectedPlatforms, activePlatform]);

//   // ============================================================
//   // PLATFORM DEFINITION
//   // ============================================================

//   const platform = platforms.find((item) => item.id === activePlatform);

//   // ============================================================
//   // CONTENT TYPE
//   // ============================================================

//   // const contentType =
//   //   activePlatform
//   //     ? platformContentTypes[
//   //         activePlatform
//   //       ] || ""
//   //     : "";
//   const contentType = activePlatform
//     ? platformContentTypes[activePlatform] || ""
//     : "";

//   // ============================================================
//   // RENDER
//   // ============================================================

//   return (
//     <Paper
//       elevation={0}
//       sx={{
//         border: "1px solid #E2E8F0",

//         borderRadius: "24px",

//         bgcolor: "#FFFFFF",

//         overflow: "hidden",
//       }}
//     >
//       {/* ======================================================
//           HEADER
//       ====================================================== */}

//       <Box
//         sx={{
//           px: 3,
//           pt: 3,
//           pb: 2,

//           borderBottom: "1px solid #F1F5F9",
//         }}
//       >
//         <Typography sx={TYPOGRAPHY.sectionTitle}>Live Preview</Typography>

//         <Typography
//           sx={{
//             ...TYPOGRAPHY.sectionDescription,
//             mt: 0.5,
//           }}
//         >
//           See how your post will look before publishing.
//         </Typography>
//       </Box>

//       {/* ======================================================
//           PLATFORM TABS
//       ====================================================== */}

//       <PreviewPlatformTabs
//         platforms={selectedPlatforms}
//         value={activePlatform}
//         onChange={setActivePlatform}
//       />

//       {/* ======================================================
//           PREVIEW
//       ====================================================== */}

//       <Box
//         sx={{
//           p: 3,

//           minHeight: 500,

//           bgcolor: "#FFFFFF",
//         }}
//       >
//         {/* <PreviewPostCard
//           organization={organization}
//           platform={platform}
//           contentType={contentType}
//           caption={caption}
//           media={media}
//         /> */}
//         <PreviewPostCard
//           organization={organization}
//           platform={platform}
//           contentType={contentType}
//           caption={caption}
//           media={media}
//         />
//       </Box>
//     </Paper>
//   );
// }

import { Box, Paper, Typography } from "@mui/material";

import { useFormContext } from "react-hook-form";

import { useEffect, useMemo, useState } from "react";

import { TYPOGRAPHY } from "../../../theme/typography";

import PreviewPlatformTabs from "./preview/PreviewPlatformTabs";
import PreviewPostCard from "./preview/PreviewPostCard";

export default function LivePreviewSection({
  organizations = [],
  platforms = [],
  accounts = [],
}) {
  const { watch } = useFormContext();

  // ============================================================
  // FORM STATE
  // ============================================================

  const organizationId = watch("organization") || "";

  const selectedPlatforms = watch("platforms") || [];

  const selectedAccountIds = watch("social_account_ids") || [];

  const platformContentTypes = watch("platform_content_types") || {};

  const caption = watch("caption") || "";

  const media = watch("media") || [];

  // ============================================================
  // ORGANIZATION
  // ============================================================

  const organization = organizations.find((item) => item.id === organizationId);

  // ============================================================
  // SELECTED ACCOUNTS
  // ============================================================

  const selectedAccounts = useMemo(() => {
    if (!Array.isArray(accounts) || !Array.isArray(selectedAccountIds)) {
      return [];
    }

    return accounts.filter((account) =>
      selectedAccountIds.includes(account?.id),
    );
  }, [accounts, selectedAccountIds]);

  // ============================================================
  // ACTIVE PLATFORM
  // ============================================================

  const [activePlatform, setActivePlatform] = useState("");

  // ============================================================
  // KEEP ACTIVE PLATFORM VALID
  // ============================================================

  useEffect(() => {
    if (!selectedPlatforms.length) {
      setActivePlatform("");
      return;
    }

    if (!selectedPlatforms.includes(activePlatform)) {
      setActivePlatform(selectedPlatforms[0]);
    }
  }, [selectedPlatforms, activePlatform]);

  // ============================================================
  // PLATFORM DEFINITION
  // ============================================================

  const platform = platforms.find((item) => item.id === activePlatform);

  // ============================================================
  // ACCOUNTS FOR ACTIVE PLATFORM
  // ============================================================

  const activePlatformAccounts = useMemo(() => {
    if (!activePlatform) {
      return [];
    }

    return selectedAccounts.filter((account) => {
      const accountPlatform = String(account?.platform || "").toUpperCase();

      return accountPlatform === activePlatform;
    });
  }, [activePlatform, selectedAccounts]);

  // ============================================================
  // CONTENT TYPE
  // ============================================================

  const contentType = activePlatform
    ? platformContentTypes[activePlatform] || ""
    : "";

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Paper
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",

        borderRadius: "24px",

        bgcolor: "#FFFFFF",

        overflow: "hidden",
      }}
    >
      {/* ======================================================
          HEADER
      ====================================================== */}

      <Box
        sx={{
          px: 3,
          pt: 3,
          pb: 2,

          borderBottom: "1px solid #F1F5F9",
        }}
      >
        <Typography sx={TYPOGRAPHY.sectionTitle}>Live Preview</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.5,
          }}
        >
          See how your post will look before publishing.
        </Typography>
      </Box>

      {/* ======================================================
          PLATFORM TABS
      ====================================================== */}

      {selectedPlatforms.length > 0 && (
        <PreviewPlatformTabs
          platforms={selectedPlatforms}
          value={activePlatform}
          onChange={setActivePlatform}
        />
      )}

      {/* ======================================================
          PREVIEW
      ====================================================== */}

      <Box
        sx={{
          p: 3,

          minHeight: 500,

          bgcolor: "#FFFFFF",
        }}
      >
        <PreviewPostCard
          organization={organization}
          platform={platform}
          accounts={activePlatformAccounts}
          contentType={contentType}
          caption={caption}
          media={media}
        />
      </Box>
    </Paper>
  );
}
