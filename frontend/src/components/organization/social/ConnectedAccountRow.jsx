// import { Avatar, Box, Button, Chip, Stack, Typography } from "@mui/material";

// import InstagramIcon from "@mui/icons-material/Instagram";
// import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
// import LinkedInIcon from "@mui/icons-material/LinkedIn";
// import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
// import YouTubeIcon from "@mui/icons-material/YouTube";
// import XIcon from "@mui/icons-material/X";
// import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

// const platformIcons = {
//   instagram: InstagramIcon,
//   facebook: FacebookRoundedIcon,
//   linkedin: LinkedInIcon,
//   threads: SmartToyOutlinedIcon,
//   youtube: YouTubeIcon,
//   x: XIcon,
// };

// export default function ConnectedAccountRow({ account }) {
//   const Icon = platformIcons[account.platform];

//   return (
//     <Box
//       sx={{
//         mt: 2,

//         px: 2.5,
//         py: 2,

//         border: "1px solid #E2E8F0",

//         borderRadius: "18px",

//         display: "flex",

//         justifyContent: "space-between",

//         alignItems: "center",

//         transition: ".25s",

//         "&:hover": {
//           boxShadow: "0 8px 20px rgba(15,23,42,.05)",
//         },
//       }}
//     >
//       {/* LEFT */}

//       <Stack direction="row" spacing={2} alignItems="center">
//         <Avatar
//           sx={{
//             width: 50,
//             height: 50,

//             bgcolor: "#F8FAFC",
//           }}
//         >
//           {Icon && (
//             <Icon
//               sx={{
//                 color: "#111827",
//               }}
//             />
//           )}
//         </Avatar>

//         <Box>
//           <Typography
//             sx={{
//               fontSize: 16,
//               fontWeight: 600,
//               color: "#1E293B",
//             }}
//           >
//             {account.pageName}
//           </Typography>

//           <Typography
//             sx={{
//               mt: 0.3,
//               fontSize: 14,
//               color: "#64748B",
//             }}
//           >
//             {account.username} • {account.lastSync}
//           </Typography>
//         </Box>
//       </Stack>

//       {/* RIGHT */}

//       <Stack direction="row" spacing={1.5} alignItems="center">
//         <Chip
//           label={account.connected ? "Connected" : "Disconnected"}
//           size="small"
//           sx={{
//             bgcolor: account.connected ? "#ECFDF3" : "#F1F5F9",

//             color: account.connected ? "#059669" : "#64748B",

//             border: "1px solid",

//             borderColor: account.connected ? "#A7F3D0" : "#CBD5E1",

//             fontWeight: 600,
//           }}
//         />

//         <Chip
//           label={account.valid ? "Valid" : "Expired"}
//           size="small"
//           sx={{
//             bgcolor: account.valid ? "#ECFDF3" : "#FEF2F2",

//             color: account.valid ? "#059669" : "#DC2626",

//             border: "1px solid",

//             borderColor: account.valid ? "#A7F3D0" : "#FECACA",

//             fontWeight: 600,
//           }}
//         />

//         {account.connected ? (
//           <Button
//             startIcon={<CloseRoundedIcon />}
//             sx={{
//               color: "#475569",

//               textTransform: "none",

//               fontWeight: 500,
//             }}
//           >
//             Disconnect
//           </Button>
//         ) : (
//           <Button
//             variant="outlined"
//             sx={{
//               borderRadius: "12px",

//               textTransform: "none",
//             }}
//           >
//             Reconnect
//           </Button>
//         )}
//       </Stack>
//     </Box>
//   );
// }

import { Avatar, Box, Button, Chip, Stack, Typography } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import YouTubeIcon from "@mui/icons-material/YouTube";
import XIcon from "@mui/icons-material/X";

const platformIcons = {
  instagram: InstagramIcon,
  facebook: FacebookRoundedIcon,
  linkedin: LinkedInIcon,
  threads: SmartToyOutlinedIcon,
  youtube: YouTubeIcon,
  x: XIcon,
};

export default function ConnectedAccountRow({ account }) {
  const Icon = platformIcons[account?.platform];

  // ==========================================================
  // LAST SYNC FORMATTER
  // ==========================================================

  const formatLastSync = (value) => {
    if (!value) {
      return "Not synced yet";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return `Last synced ${date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    })}`;
  };

  // ==========================================================
  // PLATFORM NAME
  // ==========================================================

  const platformName = account?.platform
    ? account.platform.charAt(0).toUpperCase() + account.platform.slice(1)
    : "Social Account";

  return (
    <Box
      sx={{
        mt: 2,

        px: 2.5,
        py: 2,

        border: "1px solid #E2E8F0",

        borderRadius: "18px",

        display: "flex",

        justifyContent: "space-between",

        alignItems: "center",

        gap: 2,

        transition: "box-shadow .2s ease",

        "&:hover": {
          boxShadow: "0 8px 20px rgba(15,23,42,.05)",
        },
      }}
    >
      {/* ======================================================
          LEFT
      ====================================================== */}

      <Stack direction="row" spacing={2} alignItems="center" minWidth={0}>
        <Avatar
          sx={{
            width: 50,
            height: 50,
            bgcolor: "#F8FAFC",
            flexShrink: 0,
          }}
        >
          {Icon && (
            <Icon
              sx={{
                color: "#111827",
              }}
            />
          )}
        </Avatar>

        <Box minWidth={0}>
          <Typography
            sx={{
              fontSize: 16,
              fontWeight: 600,
              color: "#1E293B",
            }}
          >
            {account?.pageName || platformName}
          </Typography>

          <Typography
            sx={{
              mt: 0.3,
              fontSize: 14,
              color: "#64748B",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              maxWidth: {
                xs: 180,
                sm: 300,
                md: 420,
              },
            }}
          >
            {account?.username ? `${account.username} • ` : ""}
            {formatLastSync(account?.lastSync)}
          </Typography>
        </Box>
      </Stack>

      {/* ======================================================
          RIGHT
      ====================================================== */}

      <Stack direction="row" spacing={1.5} alignItems="center" flexShrink={0}>
        {/* Connection Status */}

        <Chip
          label={account?.connected ? "Connected" : "Disconnected"}
          size="small"
          sx={{
            bgcolor: account?.connected ? "#ECFDF3" : "#F1F5F9",

            color: account?.connected ? "#059669" : "#64748B",

            border: "1px solid",

            borderColor: account?.connected ? "#A7F3D0" : "#CBD5E1",

            fontWeight: 600,
          }}
        />

        {/* Token / Account Validity */}

        <Chip
          label={account?.valid ? "Valid" : "Expired"}
          size="small"
          sx={{
            bgcolor: account?.valid ? "#ECFDF3" : "#FEF2F2",

            color: account?.valid ? "#059669" : "#DC2626",

            border: "1px solid",

            borderColor: account?.valid ? "#A7F3D0" : "#FECACA",

            fontWeight: 600,
          }}
        />

        {/* Action */}

        {account?.connected ? (
          <Button
            variant="text"
            disabled
            sx={{
              textTransform: "none",
              fontWeight: 500,
              minWidth: 92,
            }}
          >
            Connected
          </Button>
        ) : (
          <Button
            variant="outlined"
            disabled
            sx={{
              borderRadius: "12px",
              textTransform: "none",
              minWidth: 92,
            }}
          >
            Reconnect
          </Button>
        )}
      </Stack>
    </Box>
  );
}
