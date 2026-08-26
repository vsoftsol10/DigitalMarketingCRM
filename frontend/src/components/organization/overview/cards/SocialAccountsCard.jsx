// import {
//   Box,
//   Card,
//   CardContent,
//   Divider,
//   Stack,
//   Typography,
// } from "@mui/material";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// import { SOCIAL_PLATFORMS } from "../../../../constants/social/socialPlatforms";

// import SocialPlatformCard from "../../../ui/SocialPlatformCard";

// import ConnectedAccountRow from "../../social/ConnectedAccountRow";

// export default function SocialAccountsCard({ organization }) {
//   // ============================================================
//   // CONNECTED ACCOUNTS
//   // ============================================================

//   const connectedAccounts = Array.isArray(organization?.social_accounts)
//     ? organization.social_accounts
//     : [];

//   const activeConnectedAccounts = connectedAccounts.filter(
//     (account) => account.connected,
//   );

//   const connectedPlatforms = activeConnectedAccounts.map(
//     (account) => account.platform,
//   );

//   const connectedCount = activeConnectedAccounts.length;

//   // ============================================================
//   // RENDER
//   // ============================================================

//   return (
//     <Card
//       elevation={0}
//       sx={{
//         border: "1px solid #E2E8F0",
//         borderRadius: "20px",
//       }}
//     >
//       <CardContent
//         sx={{
//           p: 3,
//         }}
//       >
//         {/* ======================================================
//             HEADER
//         ====================================================== */}

//         <Typography sx={TYPOGRAPHY.sectionTitle}>
//           Connected Social Accounts
//         </Typography>

//         <Typography
//           sx={{
//             ...TYPOGRAPHY.sectionDescription,
//             mb: 3,
//           }}
//         >
//           {connectedCount} {connectedCount === 1 ? "account" : "accounts"}{" "}
//           connected
//         </Typography>

//         <Divider />

//         {/* ======================================================
//             CONNECTED ACCOUNT LIST
//         ====================================================== */}

//         {connectedAccounts.length > 0 && (
//           <Box
//             sx={{
//               mt: 1,
//             }}
//           >
//             {connectedAccounts.map((account) => (
//               <ConnectedAccountRow
//                 key={account.id}
//                 account={{
//                   platform: account.platform,

//                   pageName: account.page_name,

//                   username: account.username,

//                   connected: account.connected,

//                   valid: account.valid ?? true,

//                   lastSync: account.last_sync ?? "Not synced yet",
//                 }}
//               />
//             ))}
//           </Box>
//         )}

//         {/* ======================================================
//             EMPTY STATE
//         ====================================================== */}

//         {connectedAccounts.length === 0 && (
//           <Box
//             sx={{
//               py: 5,
//               textAlign: "center",
//             }}
//           >
//             <Typography
//               sx={{
//                 fontSize: 15,
//                 fontWeight: 500,
//                 color: "#64748B",
//               }}
//             >
//               No social accounts connected yet.
//             </Typography>

//             <Typography
//               sx={{
//                 mt: 0.5,
//                 fontSize: 13,
//                 color: "#94A3B8",
//               }}
//             >
//               Connect an account to manage social publishing and insights.
//             </Typography>
//           </Box>
//         )}

//         {/* ======================================================
//             CONNECT NEW ACCOUNT
//         ====================================================== */}

//         <Typography
//           sx={{
//             mt: 4,
//             mb: 2,
//             fontSize: 15,
//             fontWeight: 600,
//             color: "#475569",
//           }}
//         >
//           Connect a new account
//         </Typography>

//         <Box
//           sx={{
//             display: "flex",
//             flexWrap: "wrap",
//             gap: 2,
//           }}
//         >
//           {SOCIAL_PLATFORMS.map((platform) => (
//             <SocialPlatformCard
//               key={platform.id}
//               {...platform}
//               selected={false}
//               disabled={connectedPlatforms.includes(platform.id)}
//               onClick={() => {
//                 // OAuth connection will be
//                 // implemented here later.
//               }}
//             />
//           ))}
//         </Box>
//       </CardContent>
//     </Card>
//   );
// }

import { Box } from "@mui/material";

import SocialAccountsSection from "../../social/SocialAccountsSection";

// ============================================================
// SOCIAL ACCOUNTS CARD
// ============================================================
//
// Organization Overview wrapper.
//
// IMPORTANT:
//
// The actual Social Accounts UI is owned by:
//
// components/organization/social/SocialAccountsSection.jsx
//
// This component only adapts the Overview page data into that
// reusable component.
//
// No duplicated platform cards.
// No duplicated connected-account rows.
// No duplicated empty state.
// No OAuth logic here.
//
// ============================================================

export default function SocialAccountsCard({ organization }) {
  // ============================================================
  // ORGANIZATION ID
  // ============================================================

  const organizationId =
    organization?.organization_id || organization?.id || null;

  // ============================================================
  // SOCIAL ACCOUNTS
  // ============================================================
  //
  // If Overview API already returns social_accounts, we pass
  // them directly.
  //
  // The reusable SocialAccountsSection handles presentation.
  //
  // ============================================================

  const socialAccounts = Array.isArray(organization?.social_accounts)
    ? organization.social_accounts
    : [];

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Box
      sx={{
        width: "100%",
      }}
    >
      <SocialAccountsSection
        mode="overview"
        organizationId={organizationId}
        accounts={socialAccounts}
      />
    </Box>
  );
}
