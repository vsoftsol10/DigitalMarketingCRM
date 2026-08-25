// import { Box, Card, CardContent, Divider, Typography } from "@mui/material";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// import { SOCIAL_PLATFORMS } from "../../../../constants/social/socialPlatforms";

// import SocialPlatformCard from "../../../ui/SocialPlatformCard";

// import ConnectedAccountRow from "../../social/ConnectedAccountRow";

// export default function SocialAccountsCard({ organization }) {
//   const connectedAccounts = organization?.social_accounts || [];
//   const connectedPlatforms = connectedAccounts.map(
//     (account) => account.platform,
//   );
//   return (
//     <Card
//       elevation={0}
//       sx={{
//         border: "1px solid #E2E8F0",

//         borderRadius: "20px",
//       }}
//     >
//       <CardContent>
//         <Typography sx={TYPOGRAPHY.sectionTitle}>
//           Connected Social Accounts
//         </Typography>

//         <Typography
//           sx={{
//             ...TYPOGRAPHY.sectionDescription,

//             mb: 3,
//           }}
//         >
//           {connectedAccounts.filter((x) => x.connected).length} of{" "}
//           {connectedAccounts.length} connected
//         </Typography>

//         <Divider />

//         <Box
//           sx={{
//             mt: 1,
//           }}
//         >
//           {/* {connectedAccounts.map((account) => (
//             <ConnectedAccountRow key={account.id} account={account} />
//           ))} */}
//           {connectedAccounts.map((account) => (
//             <ConnectedAccountRow
//               key={account.platform}
//               account={{
//                 platform: account.platform,

//                 pageName: account.page_name,

//                 username: account.username,

//                 connected: account.connected,

//                 valid: account.valid ?? true,

//                 lastSync: account.last_sync ?? "Just now",
//               }}
//             />
//           ))}
//         </Box>

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
//             display: "grid",

//             // gridTemplateColumns: {
//             //   xs: "repeat(2,1fr)",
//             //   sm: "repeat(3,1fr)",
//             //   md: "repeat(4,1fr)",
//             //   lg: "repeat(6,1fr)",
//             // },
//             display: "flex",
//             flexWrap: "wrap",
//             justifyContent: "space-between",
//             gap: 2,
//             // gap: 2,
//           }}
//         >
//           {SOCIAL_PLATFORMS.map((platform) => (
//             <SocialPlatformCard
//               key={platform.id}
//               {...platform}
//               selected={false}
//               disabled={connectedPlatforms.includes(platform.id)}
//               onClick={() => console.log(platform.id)}
//             />
//           ))}
//         </Box>
//       </CardContent>
//     </Card>
//   );
// }

import {
  Box,
  Card,
  CardContent,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import { TYPOGRAPHY } from "../../../../theme/typography";

import { SOCIAL_PLATFORMS } from "../../../../constants/social/socialPlatforms";

import SocialPlatformCard from "../../../ui/SocialPlatformCard";

import ConnectedAccountRow from "../../social/ConnectedAccountRow";

export default function SocialAccountsCard({
  organization,
}) {
  // ============================================================
  // CONNECTED ACCOUNTS
  // ============================================================

  const connectedAccounts = Array.isArray(
    organization?.social_accounts,
  )
    ? organization.social_accounts
    : [];

  const activeConnectedAccounts =
    connectedAccounts.filter(
      (account) => account.connected,
    );

  const connectedPlatforms =
    activeConnectedAccounts.map(
      (account) => account.platform,
    );

  const connectedCount =
    activeConnectedAccounts.length;

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "20px",
      }}
    >
      <CardContent
        sx={{
          p: 3,
        }}
      >
        {/* ======================================================
            HEADER
        ====================================================== */}

        <Typography
          sx={TYPOGRAPHY.sectionTitle}
        >
          Connected Social Accounts
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mb: 3,
          }}
        >
          {connectedCount}{" "}
          {connectedCount === 1
            ? "account"
            : "accounts"}{" "}
          connected
        </Typography>

        <Divider />

        {/* ======================================================
            CONNECTED ACCOUNT LIST
        ====================================================== */}

        {connectedAccounts.length > 0 && (
          <Box
            sx={{
              mt: 1,
            }}
          >
            {connectedAccounts.map(
              (account) => (
                <ConnectedAccountRow
                  key={account.id}
                  account={{
                    platform:
                      account.platform,

                    pageName:
                      account.page_name,

                    username:
                      account.username,

                    connected:
                      account.connected,

                    valid:
                      account.valid ?? true,

                    lastSync:
                      account.last_sync ??
                      "Not synced yet",
                  }}
                />
              ),
            )}
          </Box>
        )}

        {/* ======================================================
            EMPTY STATE
        ====================================================== */}

        {connectedAccounts.length === 0 && (
          <Box
            sx={{
              py: 5,
              textAlign: "center",
            }}
          >
            <Typography
              sx={{
                fontSize: 15,
                fontWeight: 500,
                color: "#64748B",
              }}
            >
              No social accounts connected yet.
            </Typography>

            <Typography
              sx={{
                mt: 0.5,
                fontSize: 13,
                color: "#94A3B8",
              }}
            >
              Connect an account to manage
              social publishing and insights.
            </Typography>
          </Box>
        )}

        {/* ======================================================
            CONNECT NEW ACCOUNT
        ====================================================== */}

        <Typography
          sx={{
            mt: 4,
            mb: 2,
            fontSize: 15,
            fontWeight: 600,
            color: "#475569",
          }}
        >
          Connect a new account
        </Typography>

        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            gap: 2,
          }}
        >
          {SOCIAL_PLATFORMS.map(
            (platform) => (
              <SocialPlatformCard
                key={platform.id}
                {...platform}
                selected={false}
                disabled={connectedPlatforms.includes(
                  platform.id,
                )}
                onClick={() => {
                  // OAuth connection will be
                  // implemented here later.
                }}
              />
            ),
          )}
        </Box>
      </CardContent>
    </Card>
  );
}