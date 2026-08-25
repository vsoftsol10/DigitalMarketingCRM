// import {
//   Box,
//   Card,
//   CardContent,
//   Divider,
//   Grid,
//   Stack,
//   Typography,
//   Chip,
// } from "@mui/material";

// import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
// import LanguageOutlinedIcon from "@mui/icons-material/LanguageOutlined";
// import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
// import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
// import RestaurantOutlinedIcon from "@mui/icons-material/RestaurantOutlined";
// import LocationOnOutlinedIcon from "@mui/icons-material/LocationOnOutlined";
// import PaidOutlinedIcon from "@mui/icons-material/PaidOutlined";
// import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// export default function BrandInformationCard({ organization }) {
//   // const information = [
//   //   {
//   //     icon: BusinessOutlinedIcon,
//   //     label: "Organization",
//   //     value: organization.name,
//   //   },
//   //   {
//   //     icon: RestaurantOutlinedIcon,
//   //     label: "Industry",
//   //     value: organization.industry,
//   //   },
//   //   {
//   //     icon: LanguageOutlinedIcon,
//   //     label: "Website",
//   //     value: organization.website,
//   //   },
//   //   {
//   //     icon: LocationOnOutlinedIcon,
//   //     label: "Location",
//   //     value: organization.location,
//   //   },
//   //   {
//   //     icon: GroupsOutlinedIcon,
//   //     label: "Followers",
//   //     value: "48.2K",
//   //   },
//   //   {
//   //     icon: PaidOutlinedIcon,
//   //     label: "Monthly Budget",
//   //     value: "$8,500",
//   //   },
//   //   {
//   //     icon: LightbulbOutlinedIcon,
//   //     label: "Content Ideas",
//   //     value: "3",
//   //   },
//   //   {
//   //     icon: ShareOutlinedIcon,
//   //     label: "Social Accounts",
//   //     value: "2 connected",
//   //   },
//   // ];

//   const information = [
//     {
//       icon: BusinessOutlinedIcon,
//       label: "Organization",
//       value: organization?.name || "-",
//     },
//     {
//       icon: RestaurantOutlinedIcon,
//       label: "Industry",
//       value: organization?.industry || "-",
//     },
//     {
//       icon: LanguageOutlinedIcon,
//       label: "Website",
//       value: organization?.website || "-",
//     },
//     {
//       icon: LocationOnOutlinedIcon,
//       label: "Location",
//       value: organization?.location || "-",
//     },
//     {
//       icon: GroupsOutlinedIcon,
//       label: "Followers",
//       value: organization?.followers || "0",
//     },
//     {
//       icon: PaidOutlinedIcon,
//       label: "Monthly Budget",
//       value: organization?.monthly_budget
//         ? `$${organization.monthly_budget.toLocaleString()}`
//         : "-",
//     },
//     {
//       icon: LightbulbOutlinedIcon,
//       label: "Content Ideas",
//       value: organization?.content_ideas ?? 0,
//     },
//     {
//       icon: ShareOutlinedIcon,
//       label: "Social Accounts",
//       value: `${organization?.connected_accounts ?? 0} connected`,
//     },
//   ];
//   return (
//     <Card
//       elevation={0}
//       sx={{
//         border: "1px solid #E2E8F0",
//         borderRadius: "22px",
//       }}
//     >
//       <CardContent sx={{ p: 4 }}>
//         {/* Header */}

//         <Typography sx={TYPOGRAPHY.sectionTitle}>Brand Information</Typography>

//         <Typography
//           sx={{
//             ...TYPOGRAPHY.sectionDescription,
//             mt: 0.5,
//             mb: 4,
//           }}
//         >
//           Visual identity and positioning
//         </Typography>

//         {/* Grid */}

//         <Grid container spacing={4}>
//           {information.map((item) => {
//             const Icon = item.icon;

//             return (
//               <Grid
//                 key={item.label}
//                 size={{
//                   xs: 12,
//                   md: 6,
//                 }}
//               >
//                 <Stack direction="row" spacing={2} alignItems="center">
//                   <Icon
//                     sx={{
//                       color: "#94A3B8",
//                       fontSize: 20,
//                     }}
//                   />

//                   <Box>
//                     <Typography
//                       sx={{
//                         fontSize: 13,
//                         color: "#94A3B8",
//                       }}
//                     >
//                       {item.label}
//                     </Typography>

//                     <Typography
//                       sx={{
//                         ...TYPOGRAPHY.body,
//                         mt: 0.3,
//                         fontWeight: 500,
//                       }}
//                     >
//                       {item.value}
//                     </Typography>
//                   </Box>
//                 </Stack>
//               </Grid>
//             );
//           })}
//         </Grid>

//         <Divider sx={{ my: 4 }} />

//         {/* Bio */}

//         <Typography
//           sx={{
//             fontSize: 13,
//             color: "#94A3B8",
//             mb: 1,
//           }}
//         >
//           Bio
//         </Typography>

//         <Typography
//           sx={{
//             ...TYPOGRAPHY.body,
//             lineHeight: 1.8,
//           }}
//         >
//           {/* {organization.description} */}
//           {organization?.description || "-"}
//         </Typography>

//         <Divider sx={{ my: 4 }} />

//         {/* Logo */}

//         <Stack direction="row" spacing={2} alignItems="center">
//           <Typography
//             sx={{
//               fontSize: 13,
//               color: "#94A3B8",
//               width: 90,
//             }}
//           >
//             Logo Color
//           </Typography>

//           <Box
//             sx={{
//               width: 28,
//               height: 28,
//               borderRadius: "50%",
//               // bgcolor: organization.logo_color,
//               bgcolor: organization?.logo_color || "#CBD5E1",
//               border: "3px solid white",
//               boxShadow: "0 0 0 1px #CBD5E1",
//             }}
//           />

//           <Chip
//             size="small"
//             // label={organization.status}
//             label={organization?.subscription_status || "-"}
//             sx={{
//               bgcolor: "#ECFDF3",
//               color: "#16A34A",
//               fontWeight: 600,
//               textTransform: "capitalize",
//             }}
//           />
//         </Stack>
//       </CardContent>
//     </Card>
//   );
// }

import {
  Box,
  Card,
  CardContent,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";

import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import LanguageOutlinedIcon from "@mui/icons-material/LanguageOutlined";
import LocationOnOutlinedIcon from "@mui/icons-material/LocationOnOutlined";
import RestaurantOutlinedIcon from "@mui/icons-material/RestaurantOutlined";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function BrandInformationCard({ organization }) {
  // ============================================================
  // CONNECTED SOCIAL ACCOUNT COUNT
  // ============================================================

  const connectedAccountCount = Array.isArray(organization?.social_accounts)
    ? organization.social_accounts.filter((account) => account.connected).length
    : 0;

  // ============================================================
  // ORGANIZATION INFORMATION
  // ============================================================

  const information = [
    {
      icon: BusinessOutlinedIcon,
      label: "Organization",
      value: organization?.name || "-",
    },
    {
      icon: RestaurantOutlinedIcon,
      label: "Industry",
      value: organization?.industry || "-",
    },
    {
      icon: LanguageOutlinedIcon,
      label: "Website",
      value: organization?.website || "-",
    },
    {
      icon: LocationOnOutlinedIcon,
      label: "Location",
      value: organization?.location || "-",
    },
    {
      icon: ShareOutlinedIcon,
      label: "Connected Social Accounts",
      value: `${connectedAccountCount} connected`,
    },
  ];

  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "22px",
      }}
    >
      <CardContent
        sx={{
          p: 4,
        }}
      >
        {/* =====================================================
            HEADER
        ===================================================== */}

        <Typography sx={TYPOGRAPHY.sectionTitle}>Brand Information</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.5,
            mb: 4,
          }}
        >
          Organization identity and information
        </Typography>

        {/* =====================================================
            INFORMATION GRID
        ===================================================== */}

        <Grid container spacing={4}>
          {information.map((item) => {
            const Icon = item.icon;

            return (
              <Grid
                key={item.label}
                size={{
                  xs: 12,
                  md: 6,
                }}
              >
                <Stack direction="row" spacing={2} alignItems="center">
                  <Icon
                    sx={{
                      color: "#94A3B8",
                      fontSize: 20,
                      flexShrink: 0,
                    }}
                  />

                  <Box minWidth={0}>
                    <Typography
                      sx={{
                        fontSize: 13,
                        color: "#94A3B8",
                      }}
                    >
                      {item.label}
                    </Typography>

                    <Typography
                      sx={{
                        ...TYPOGRAPHY.body,
                        mt: 0.3,
                        fontWeight: 500,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {item.value}
                    </Typography>
                  </Box>
                </Stack>
              </Grid>
            );
          })}
        </Grid>

        {/* =====================================================
            DESCRIPTION
        ===================================================== */}

        <Divider
          sx={{
            my: 4,
          }}
        />

        <Typography
          sx={{
            fontSize: 13,
            color: "#94A3B8",
            mb: 1,
          }}
        >
          Description
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.body,
            lineHeight: 1.8,
            color: "#334155",
          }}
        >
          {organization?.description || "-"}
        </Typography>

        {/* =====================================================
            LOGO COLOR
        ===================================================== */}

        <Divider
          sx={{
            my: 4,
          }}
        />

        <Stack direction="row" spacing={2} alignItems="center">
          <Typography
            sx={{
              fontSize: 13,
              color: "#94A3B8",
              width: 90,
              flexShrink: 0,
            }}
          >
            Logo Color
          </Typography>

          <Box
            sx={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              bgcolor: organization?.logo_color || "#CBD5E1",
              border: "3px solid #FFFFFF",
              boxShadow: "0 0 0 1px #CBD5E1",
            }}
          />
        </Stack>
      </CardContent>
    </Card>
  );
}
