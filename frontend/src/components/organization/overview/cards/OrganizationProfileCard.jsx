// import {
//   Avatar,
//   Box,
//   Card,
//   CardContent,
//   Divider,
//   Stack,
//   Typography,
// } from "@mui/material";

// import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
// import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// export default function OrganizationProfileCard({ organization }) {
//   const initials =
//     organization?.name
//       ?.split(" ")
//       .filter(Boolean)
//       .map((word) => word[0])
//       .join("")
//       .substring(0, 2)
//       .toUpperCase() || "--";

//   const connectedAccountCount = Array.isArray(organization?.social_accounts)
//     ? organization.social_accounts.filter((account) => account.connected).length
//     : 0;

//   const clientSince = organization?.created_at
//     ? new Date(organization.created_at).toLocaleDateString("en-US", {
//         month: "short",
//         day: "numeric",
//         year: "numeric",
//       })
//     : "-";

//   const isActive = organization?.organization_status === "ACTIVE";

//   const organizationStatus = isActive ? "Active" : "Inactive";

//   const statusStyles = isActive
//     ? {
//         dot: "#16A34A",
//         text: "#15803D",
//         background: "#F0FDF4",
//         border: "#BBF7D0",
//       }
//     : {
//         dot: "#64748B",
//         text: "#475569",
//         background: "#F8FAFC",
//         border: "#CBD5E1",
//       };

//   const subscriptionPlan = organization?.subscription_plan
//     ? organization.subscription_plan.charAt(0).toUpperCase() +
//       organization.subscription_plan.slice(1).toLowerCase()
//     : "-";

//   const summaryItems = [
//     {
//       icon: CalendarTodayOutlinedIcon,
//       label: "Client Since",
//       value: clientSince,
//     },
//     {
//       icon: ShareOutlinedIcon,
//       label: "Connected Accounts",
//       value: `${connectedAccountCount} ${
//         connectedAccountCount === 1 ? "connected" : "connected"
//       }`,
//     },
//   ];

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

//           "&:last-child": {
//             pb: 3,
//           },
//         }}
//       >
//         {/* ==================================================
//             PROFILE HEADER
//         ================================================== */}

//         <Stack direction="row" spacing={2} alignItems="center">
//           <Avatar
//             sx={{
//               width: 64,
//               height: 64,
//               bgcolor: organization?.logo_color || "#2563EB",
//               fontSize: 28,
//               fontWeight: 700,
//               flexShrink: 0,
//             }}
//           >
//             {initials}
//           </Avatar>

//           <Box flex={1} minWidth={0}>
//             <Typography
//               sx={{
//                 ...TYPOGRAPHY.cardTitle,
//                 fontSize: 18,
//                 fontWeight: 700,
//                 overflow: "hidden",
//                 textOverflow: "ellipsis",
//                 whiteSpace: "nowrap",
//               }}
//             >
//               {organization?.name || "-"}
//             </Typography>

//             <Typography
//               sx={{
//                 mt: 0.5,
//                 fontSize: 13,
//                 color: "#94A3B8",
//               }}
//             >
//               Organization profile
//             </Typography>
//           </Box>
//         </Stack>

//         <Divider
//           sx={{
//             my: 3,
//           }}
//         />

//         {/* ==================================================
//             SUBSCRIPTION PLAN
//         ================================================== */}

//         <Box>
//           <Typography
//             sx={{
//               fontSize: 12,
//               fontWeight: 600,
//               color: "#94A3B8",
//               textTransform: "uppercase",
//               letterSpacing: "0.04em",
//             }}
//           >
//             Subscription Plan
//           </Typography>

//           <Typography
//             sx={{
//               mt: 0.75,
//               fontSize: 17,
//               fontWeight: 700,
//               color: "#0F172A",
//             }}
//           >
//             {subscriptionPlan}
//           </Typography>
//         </Box>

//         {/* ==================================================
//             ORGANIZATION STATUS
//         ================================================== */}

//         <Box
//           sx={{
//             mt: 2.5,
//           }}
//         >
//           <Typography
//             sx={{
//               fontSize: 12,
//               fontWeight: 600,
//               color: "#94A3B8",
//               textTransform: "uppercase",
//               letterSpacing: "0.04em",
//             }}
//           >
//             Organization Status
//           </Typography>

//           <Box
//             sx={{
//               mt: 0.75,
//               display: "inline-flex",
//               alignItems: "center",
//               gap: 1,
//               px: 1.25,
//               py: 0.75,
//               borderRadius: "999px",
//               bgcolor: statusStyles.background,
//               border: "1px solid",
//               borderColor: statusStyles.border,
//             }}
//           >
//             <Box
//               sx={{
//                 width: 7,
//                 height: 7,
//                 borderRadius: "50%",
//                 bgcolor: statusStyles.dot,
//               }}
//             />

//             <Typography
//               sx={{
//                 fontSize: 13,
//                 fontWeight: 600,
//                 color: statusStyles.text,
//               }}
//             >
//               {organizationStatus}
//             </Typography>
//           </Box>
//         </Box>

//         <Divider
//           sx={{
//             my: 3,
//           }}
//         />

//         {/* ==================================================
//             SUMMARY
//         ================================================== */}

//         <Stack spacing={2.2}>
//           {summaryItems.map((item) => {
//             const Icon = item.icon;

//             return (
//               <Stack key={item.label} direction="row" alignItems="center">
//                 <Icon
//                   sx={{
//                     fontSize: 20,
//                     color: "#94A3B8",
//                     flexShrink: 0,
//                   }}
//                 />

//                 <Typography
//                   sx={{
//                     ml: 1.5,
//                     fontSize: 14,
//                     color: "#64748B",
//                   }}
//                 >
//                   {item.label}
//                 </Typography>

//                 <Typography
//                   sx={{
//                     ml: "auto",
//                     fontSize: 14,
//                     fontWeight: 600,
//                     color: "#0F172A",
//                   }}
//                 >
//                   {item.value}
//                 </Typography>
//               </Stack>
//             );
//           })}
//         </Stack>
//       </CardContent>
//     </Card>
//   );
// }

import {
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import TagOutlinedIcon from "@mui/icons-material/TagOutlined";

import { TYPOGRAPHY } from "../../../../theme/typography";

function formatDate(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatOrganizationStatus(value) {
  if (!value) {
    return "-";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function getStatusStyles(status) {
  switch (status) {
    case "ACTIVE":
      return {
        background: "#ECFDF3",
        color: "#059669",
        border: "#A7F3D0",
      };

    case "INACTIVE":
      return {
        background: "#FEF2F2",
        color: "#DC2626",
        border: "#FECACA",
      };

    default:
      return {
        background: "#F8FAFC",
        color: "#64748B",
        border: "#CBD5E1",
      };
  }
}

function DetailRow({ icon, label, value, valueColor = "#334155" }) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      sx={{
        minWidth: 0,
      }}
    >
      <Box
        sx={{
          width: 32,
          height: 32,

          borderRadius: "9px",

          backgroundColor: "#F8FAFC",
          color: "#94A3B8",

          display: "flex",
          alignItems: "center",
          justifyContent: "center",

          flexShrink: 0,

          "& svg": {
            fontSize: 17,
          },
        }}
      >
        {icon}
      </Box>

      <Typography
        sx={{
          ml: 1.25,

          fontSize: 14,
          lineHeight: "20px",
          color: "#64748B",

          flex: 1,
          minWidth: 0,
        }}
      >
        {label}
      </Typography>

      <Typography
        sx={{
          ml: 1,

          fontSize: 14,
          lineHeight: "20px",
          fontWeight: 500,

          color: valueColor,

          textAlign: "right",

          maxWidth: "55%",

          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {value}
      </Typography>
    </Stack>
  );
}

export default function OrganizationProfileCard({ organization }) {
  if (!organization) {
    return null;
  }

  const initials =
    organization.name
      ?.split(" ")
      .filter(Boolean)
      .map((word) => word[0])
      .join("")
      .substring(0, 2)
      .toUpperCase() || "--";

  const connectedAccountCount = Array.isArray(organization.social_accounts)
    ? organization.social_accounts.filter((account) => account.connected).length
    : 0;

  const organizationStatus = organization.organization_status;

  const statusStyles = getStatusStyles(organizationStatus);

  return (
    <Card
      elevation={0}
      sx={{
        width: "100%",

        border: "1px solid #E2E8F0",

        borderRadius: "20px",

        backgroundColor: "#FFFFFF",

        boxSizing: "border-box",
      }}
    >
      <CardContent
        sx={{
          p: 3,

          "&:last-child": {
            pb: 3,
          },
        }}
      >
        {/* ==================================================
            TITLE
        ================================================== */}

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionTitle,

            color: "#0F172A",
          }}
        >
          Organization Profile
        </Typography>

        {/* ==================================================
            IDENTITY (avatar-style icon block, matches SubscriptionCard)
        ================================================== */}

        <Stack
          direction="row"
          spacing={2}
          alignItems="center"
          sx={{
            mt: 3,
          }}
        >
          <Box
            sx={{
              width: 48,
              height: 48,

              borderRadius: "14px",

              backgroundColor: organization.logo_color || "#EEF4FF",

              display: "flex",
              alignItems: "center",
              justifyContent: "center",

              flexShrink: 0,
            }}
          >
            <Typography
              sx={{
                fontSize: 16,
                fontWeight: 700,
                color: "#FFFFFF",
              }}
            >
              {initials}
            </Typography>
          </Box>

          <Box
            sx={{
              minWidth: 0,
              flex: 1,
            }}
          >
            <Typography
              sx={{
                fontSize: 18,
                lineHeight: "24px",
                fontWeight: 700,

                color: "#0F172A",

                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {organization.name || "-"}
            </Typography>

            <Typography
              sx={{
                mt: 0.35,

                fontSize: 14,
                lineHeight: "20px",

                color: "#64748B",
              }}
            >
              {organization.industry || "-"}
            </Typography>
          </Box>
        </Stack>

        <Divider
          sx={{
            my: 3,
          }}
        />

        {/* ==================================================
            STATUS
        ================================================== */}

        <Box>
          <Typography
            sx={{
              fontSize: 12,
              lineHeight: "18px",
              fontWeight: 600,

              color: "#94A3B8",

              textTransform: "uppercase",

              letterSpacing: "0.04em",
            }}
          >
            Organization Status
          </Typography>

          <Chip
            label={formatOrganizationStatus(organizationStatus)}
            size="small"
            sx={{
              mt: 0.75,

              height: 30,

              borderRadius: "999px",

              backgroundColor: statusStyles.background,

              color: statusStyles.color,

              border: "1px solid",

              borderColor: statusStyles.border,

              fontSize: 13,
              fontWeight: 600,

              "& .MuiChip-label": {
                px: 1.25,
              },
            }}
          />
        </Box>

        <Divider
          sx={{
            my: 3,
          }}
        />

        {/* ==================================================
            ORGANIZATION DETAILS
        ================================================== */}

        <Stack spacing={2.2}>
          <DetailRow
            icon={<TagOutlinedIcon />}
            label="Organization ID"
            value={organization.organization_id || "-"}
          />

          <DetailRow
            icon={<BusinessOutlinedIcon />}
            label="Industry"
            value={organization.industry || "-"}
          />

          <DetailRow
            icon={<CalendarTodayOutlinedIcon />}
            label="Client Since"
            value={formatDate(organization.created_at)}
          />

          <DetailRow
            icon={<ShareOutlinedIcon />}
            label="Connected Accounts"
            value={`${connectedAccountCount} connected`}
          />
        </Stack>
      </CardContent>
    </Card>
  );
}