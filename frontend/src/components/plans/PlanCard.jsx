// import { Box, Chip, Paper, Stack, Typography } from "@mui/material";

// import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";
// import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
// import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
// import VideoLibraryOutlinedIcon from "@mui/icons-material/VideoLibraryOutlined";
// import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";

// function formatPrice(value) {
//   return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
// }

// function LimitItem({ icon, label, value }) {
//   return (
//     <Stack
//       direction="row"
//       alignItems="center"
//       spacing={0.75}
//       sx={{
//         minWidth: 0,
//       }}
//     >
//       {/* Icon */}
//       <Box
//         sx={{
//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",
//           flexShrink: 0,
//           color: "#94A3B8",
//         }}
//       >
//         {icon}
//       </Box>

//       {/* Label */}
//       <Typography
//         sx={{
//           fontSize: "14px",
//           fontWeight: 400,
//           lineHeight: "20px",
//           color: "#64748B",
//           whiteSpace: "nowrap",
//         }}
//       >
//         {label}
//       </Typography>

//       {/* Value */}
//       <Typography
//         sx={{
//           fontSize: "14px",
//           fontWeight: 600,
//           lineHeight: "20px",
//           color: "#1E293B",
//           whiteSpace: "nowrap",
//           ml: "auto",
//         }}
//       >
//         {value}
//       </Typography>
//     </Stack>
//   );
// }

// export default function PlanCard({ plan, onSelect }) {
//   const isActive = plan.status === "active";

//   const price =
//     plan.billing_cycle === "yearly" ? plan.yearly_price : plan.monthly_price;

//   const featureCount = Array.isArray(plan.features) ? plan.features.length : 0;

//   const dmAutomations = plan.limits?.dm_automations ?? 0;

//   const storage = plan.limits?.storage_gb ?? 0;

//   return (
//     <Paper
//       component="article"
//       elevation={0}
//       onClick={() => onSelect(plan)}
//       sx={{
//         width: "100%",
//         height: "300px",

//         position: "relative",

//         p: "20px 22px",

//         display: "flex",
//         flexDirection: "column",

//         border: "1px solid #DCE3EC",
//         borderRadius: "18px",

//         backgroundColor: "#FFFFFF",

//         cursor: "pointer",

//         boxSizing: "border-box",

//         transition: "border-color 160ms ease, box-shadow 160ms ease",

//         "&:hover": {
//           borderColor: "#CBD5E1",
//           boxShadow: "0 6px 18px rgba(15, 23, 42, 0.05)",
//         },
//       }}
//     >
//       {/* =====================================================
//     CARD HEADER
// ===================================================== */}

//       <Box
//         sx={{
//           width: "100%",
//           display: "flex",
//           alignItems: "flex-start",
//         }}
//       >
//         {/* LEFT SIDE */}

//         <Stack
//           direction="row"
//           alignItems="center"
//           spacing={1.25}
//           sx={{
//             minWidth: 0,
//             pr: 10,
//           }}
//         >
//           {/* Plan Icon */}

//           <Box
//             sx={{
//               width: 42,
//               height: 42,

//               flexShrink: 0,

//               display: "flex",
//               alignItems: "center",
//               justifyContent: "center",

//               borderRadius: "12px",

//               backgroundColor: "#EFF6FF",
//             }}
//           >
//             <CreditCardOutlinedIcon
//               sx={{
//                 fontSize: 21,
//                 color: "#2563EB",
//               }}
//             />
//           </Box>

//           {/* Plan Name + Type */}

//           <Box
//             sx={{
//               minWidth: 0,
//             }}
//           >
//             <Typography
//               sx={{
//                 fontSize: "17px",
//                 fontWeight: 700,
//                 lineHeight: "24px",
//                 color: "#111827",

//                 whiteSpace: "nowrap",
//                 overflow: "hidden",
//                 textOverflow: "ellipsis",
//               }}
//             >
//               {plan.name}
//             </Typography>

//             <Typography
//               sx={{
//                 fontSize: "14px",
//                 fontWeight: 400,
//                 lineHeight: "20px",

//                 color: "#94A3B8",

//                 mt: 0.15,
//               }}
//             >
//               {plan.type}
//             </Typography>
//           </Box>
//         </Stack>

//         {/* =================================================
//       STATUS — FORCE RIGHT SIDE
//   ================================================= */}

//         <Chip
//           label={isActive ? "Active" : "Inactive"}
//           size="small"
//           sx={{
//             position: "absolute",

//             top: 20,
//             right: 22,

//             height: 28,

//             border: "1px solid",

//             borderColor: isActive ? "#86EFAC" : "#CBD5E1",

//             backgroundColor: isActive ? "#F0FDF4" : "#F1F5F9",

//             color: isActive ? "#059669" : "#64748B",

//             fontSize: "12px",
//             fontWeight: 500,

//             zIndex: 2,

//             "& .MuiChip-label": {
//               px: 1.1,
//             },
//           }}
//         />
//       </Box>

//       {/* =====================================================
//           DESCRIPTION
//       ===================================================== */}

//       <Typography
//         sx={{
//           mt: 2,

//           fontSize: "14px",
//           fontWeight: 400,
//           lineHeight: "21px",

//           color: "#64748B",

//           height: "42px",

//           display: "-webkit-box",
//           WebkitLineClamp: 2,
//           WebkitBoxOrient: "vertical",
//           overflow: "hidden",
//         }}
//       >
//         {plan.description}
//       </Typography>

//       {/* =====================================================
//           PRICE
//       ===================================================== */}

//       <Stack
//         direction="row"
//         alignItems="baseline"
//         spacing={0.35}
//         sx={{
//           mt: 1.8,
//         }}
//       >
//         <Typography
//           sx={{
//             fontSize: "24px",
//             fontWeight: 700,
//             lineHeight: "32px",
//             letterSpacing: "-0.02em",

//             color: "#2563EB",
//           }}
//         >
//           ₹{formatPrice(price)}
//         </Typography>

//         <Typography
//           sx={{
//             fontSize: "13px",
//             fontWeight: 400,
//             lineHeight: "20px",

//             color: "#94A3B8",
//           }}
//         >
//           /{plan.billing_cycle === "yearly" ? "yr" : "mo"}
//         </Typography>
//       </Stack>

//       {/* =====================================================
//           DIVIDER
//       ===================================================== */}

//       <Box
//         sx={{
//           width: "100%",
//           height: "1px",

//           backgroundColor: "#E2E8F0",

//           my: 1.8,
//         }}
//       />

//       {/* =====================================================
//           LIMITS
//       ===================================================== */}

//       <Box
//         sx={{
//           display: "grid",

//           gridTemplateColumns: "1fr 1fr",

//           columnGap: 2,
//           rowGap: 1,
//         }}
//       >
//         <LimitItem
//           icon={
//             <ShareOutlinedIcon
//               sx={{
//                 fontSize: 16,
//               }}
//             />
//           }
//           label="Accounts"
//           value={plan.limits?.accounts ?? 0}
//         />

//         <LimitItem
//           icon={
//             <EditOutlinedIcon
//               sx={{
//                 fontSize: 16,
//               }}
//             />
//           }
//           label="Posts"
//           value={plan.limits?.posts ?? 0}
//         />

//         <LimitItem
//           icon={
//             <VideoLibraryOutlinedIcon
//               sx={{
//                 fontSize: 16,
//               }}
//             />
//           }
//           label="Videos"
//           value={plan.limits?.videos ?? 0}
//         />

//         <LimitItem
//           icon={
//             <CampaignOutlinedIcon
//               sx={{
//                 fontSize: 16,
//               }}
//             />
//           }
//           label="Ads"
//           value={plan.limits?.ads ?? 0}
//         />
//       </Box>

//       {/* =====================================================
//           PLAN SUMMARY
//       ===================================================== */}

//       <Typography
//         sx={{
//           mt: "auto",

//           fontSize: "13px",
//           fontWeight: 400,
//           lineHeight: "20px",

//           color: "#94A3B8",

//           whiteSpace: "nowrap",
//           overflow: "hidden",
//           textOverflow: "ellipsis",
//         }}
//       >
//         {featureCount} features
//         {"  ·  "}
//         {dmAutomations} DM automations
//         {"  ·  "}
//         {storage} GB storage
//       </Typography>
//     </Paper>
//   );
// }

import { Box, Chip, Paper, Stack, Typography } from "@mui/material";

import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import VideoLibraryOutlinedIcon from "@mui/icons-material/VideoLibraryOutlined";
import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

function LimitItem({ icon, label, value }) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={0.75}
      sx={{
        minWidth: 0,
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          color: "#94A3B8",
        }}
      >
        {icon}
      </Box>

      <Typography
        sx={{
          fontSize: "14px",
          fontWeight: 400,
          lineHeight: "20px",
          color: "#64748B",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </Typography>

      <Typography
        sx={{
          fontSize: "14px",
          fontWeight: 600,
          lineHeight: "20px",
          color: "#1E293B",
          whiteSpace: "nowrap",
          ml: "auto",
        }}
      >
        {value}
      </Typography>
    </Stack>
  );
}

function PriceItem({ label, value }) {
  return (
    <Box
      sx={{
        minWidth: 0,
      }}
    >
      <Typography
        sx={{
          fontSize: "12px",
          fontWeight: 500,
          lineHeight: "18px",
          color: "#94A3B8",
          textTransform: "uppercase",
          letterSpacing: "0.03em",
        }}
      >
        {label}
      </Typography>

      <Typography
        sx={{
          mt: 0.25,
          fontSize: "20px",
          fontWeight: 700,
          lineHeight: "28px",
          color: "#2563EB",
          whiteSpace: "nowrap",
        }}
      >
        ₹{formatPrice(value)}
      </Typography>
    </Box>
  );
}

export default function PlanCard({ plan, onSelect }) {
  const isActive = plan.status === "active";

  const limits = plan?.limits || {};

  return (
    <Paper
      component="article"
      elevation={0}
      onClick={() => onSelect(plan)}
      sx={{
        width: "100%",
        minHeight: 350,

        position: "relative",

        p: "20px 22px",

        display: "flex",
        flexDirection: "column",

        border: "1px solid #DCE3EC",
        borderRadius: "18px",

        backgroundColor: "#FFFFFF",

        cursor: "pointer",

        boxSizing: "border-box",

        transition:
          "border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease",

        "&:hover": {
          borderColor: "#CBD5E1",
          boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
          transform: "translateY(-2px)",
        },
      }}
    >
      {/* =====================================================
          HEADER
      ===================================================== */}

      <Box
        sx={{
          width: "100%",
          display: "flex",
          alignItems: "flex-start",
        }}
      >
        <Stack
          direction="row"
          alignItems="center"
          spacing={1.25}
          sx={{
            minWidth: 0,
            pr: 8,
          }}
        >
          <Box
            sx={{
              width: 42,
              height: 42,

              flexShrink: 0,

              display: "flex",
              alignItems: "center",
              justifyContent: "center",

              borderRadius: "12px",

              backgroundColor: "#EFF6FF",
            }}
          >
            <CreditCardOutlinedIcon
              sx={{
                fontSize: 21,
                color: "#2563EB",
              }}
            />
          </Box>

          <Box
            sx={{
              minWidth: 0,
            }}
          >
            <Typography
              sx={{
                fontSize: "17px",
                fontWeight: 700,
                lineHeight: "24px",
                color: "#111827",

                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {plan.name}
            </Typography>

            <Typography
              sx={{
                fontSize: "13px",
                fontWeight: 500,
                lineHeight: "20px",
                color: "#94A3B8",
                mt: 0.15,
              }}
            >
              {plan.type}
            </Typography>
          </Box>
        </Stack>

        <Chip
          label={isActive ? "Active" : "Inactive"}
          size="small"
          sx={{
            position: "absolute",

            top: 20,
            right: 22,

            height: 28,

            border: "1px solid",

            borderColor: isActive ? "#86EFAC" : "#CBD5E1",

            backgroundColor: isActive ? "#F0FDF4" : "#F1F5F9",

            color: isActive ? "#059669" : "#64748B",

            fontSize: "12px",
            fontWeight: 500,

            "& .MuiChip-label": {
              px: 1.1,
            },
          }}
        />
      </Box>

      {/* =====================================================
          DESCRIPTION
      ===================================================== */}

      <Typography
        sx={{
          mt: 2,

          fontSize: "14px",
          fontWeight: 400,
          lineHeight: "21px",

          color: "#64748B",

          minHeight: "42px",

          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {plan.description || "No description available."}
      </Typography>

      {/* =====================================================
          PRICING
      ===================================================== */}

      <Box
        sx={{
          mt: 2.25,

          display: "grid",
          gridTemplateColumns: "1fr 1fr",

          gap: 2,

          p: 1.75,

          borderRadius: "14px",

          backgroundColor: "#F8FAFC",

          border: "1px solid #E2E8F0",
        }}
      >
        <PriceItem label="Monthly" value={plan.monthly_price} />

        <PriceItem label="Yearly" value={plan.yearly_price} />
      </Box>

      {/* =====================================================
          DIVIDER
      ===================================================== */}

      <Box
        sx={{
          width: "100%",
          height: "1px",

          backgroundColor: "#E2E8F0",

          my: 2,
        }}
      />

      {/* =====================================================
          LIMITS
      ===================================================== */}

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns: "1fr 1fr",

          columnGap: 2,
          rowGap: 1.15,
        }}
      >
        <LimitItem
          icon={
            <ShareOutlinedIcon
              sx={{
                fontSize: 16,
              }}
            />
          }
          label="Accounts"
          value={limits.accounts ?? 0}
        />

        <LimitItem
          icon={
            <EditOutlinedIcon
              sx={{
                fontSize: 16,
              }}
            />
          }
          label="Posts"
          value={limits.posts ?? 0}
        />

        <LimitItem
          icon={
            <VideoLibraryOutlinedIcon
              sx={{
                fontSize: 16,
              }}
            />
          }
          label="Videos"
          value={limits.videos ?? 0}
        />

        <LimitItem
          icon={
            <CampaignOutlinedIcon
              sx={{
                fontSize: 16,
              }}
            />
          }
          label="Ads"
          value={limits.ads ?? 0}
        />
      </Box>

      {/* =====================================================
          FOOTER SUMMARY
      ===================================================== */}

      <Stack
        direction="row"
        alignItems="center"
        spacing={0.75}
        sx={{
          mt: "auto",
          pt: 2,
        }}
      >
        <AutoAwesomeOutlinedIcon
          sx={{
            fontSize: 16,
            color: "#94A3B8",
          }}
        />

        <Typography
          sx={{
            fontSize: "13px",
            fontWeight: 400,
            lineHeight: "20px",

            color: "#94A3B8",

            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {limits.dm_automations ?? 0} DM automations
        </Typography>
      </Stack>
    </Paper>
  );
}
