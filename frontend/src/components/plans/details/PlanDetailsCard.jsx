// import { Box, Paper, Stack, Typography } from "@mui/material";

// import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";
// import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
// import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
// import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
// import VideoLibraryOutlinedIcon from "@mui/icons-material/VideoLibraryOutlined";
// import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
// import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
// // import StorageOutlinedIcon from "@mui/icons-material/StorageOutlined";

// function formatPrice(value) {
//   return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
// }

// function formatDate(value) {
//   if (!value) {
//     return "—";
//   }

//   const date = new Date(value);

//   if (Number.isNaN(date.getTime())) {
//     return value;
//   }

//   return date.toLocaleDateString("en-US", {
//     month: "short",
//     day: "numeric",
//     year: "numeric",
//   });
// }

// const featureLabels = {
//   create_post: "Create Post",
//   ai_caption: "AI Caption",
//   ai_script: "AI Script",
//   content_planner: "Content Planner",
//   calendar: "Calendar",
//   dm_automation: "DM Automation",
//   ads: "Ads",
//   insights: "Insights",
// };

// function DetailItem({ icon, label, value }) {
//   return (
//     <Stack
//       direction="row"
//       alignItems="center"
//       spacing={1.25}
//       sx={{
//         minWidth: 0,
//       }}
//     >
//       <Box
//         sx={{
//           width: 34,
//           height: 34,

//           flexShrink: 0,

//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",

//           borderRadius: "9px",

//           backgroundColor: "#F8FAFC",

//           color: "#64748B",
//         }}
//       >
//         {icon}
//       </Box>

//       <Box
//         sx={{
//           minWidth: 0,
//         }}
//       >
//         <Typography
//           sx={{
//             fontSize: "13px",
//             fontWeight: 400,
//             lineHeight: "18px",
//             color: "#94A3B8",
//           }}
//         >
//           {label}
//         </Typography>

//         <Typography
//           sx={{
//             fontSize: "14px",
//             fontWeight: 500,
//             lineHeight: "20px",
//             color: "#334155",

//             overflow: "hidden",
//             textOverflow: "ellipsis",
//             whiteSpace: "nowrap",
//           }}
//         >
//           {value}
//         </Typography>
//       </Box>
//     </Stack>
//   );
// }

// export default function PlanDetailsCard({ plan }) {
//   const limits = plan?.limits || {};

//   const monthlyPrice = plan?.monthly_price ?? 0;

//   const yearlyPrice = plan?.yearly_price ?? 0;

//   return (
//     <Paper
//       elevation={0}
//       sx={{
//         width: "100%",

//         p: {
//           xs: 2.5,
//           sm: 2.75,
//         },

//         borderRadius: "18px",

//         border: "1px solid #E2E8F0",

//         backgroundColor: "#FFFFFF",

//         boxSizing: "border-box",
//       }}
//     >
//       {/* =========================
//           CARD TITLE
//       ========================= */}

//       <Typography
//         component="h2"
//         sx={{
//           fontSize: "18px",
//           fontWeight: 700,
//           lineHeight: "24px",
//           color: "#1E293B",
//           m: 0,
//         }}
//       >
//         Plan Details
//       </Typography>

//       {/* DESCRIPTION */}

//       <Typography
//         sx={{
//           fontSize: "14px",
//           fontWeight: 400,
//           lineHeight: "22px",
//           color: "#475569",

//           mt: 2,
//         }}
//       >
//         {plan.description || "—"}
//       </Typography>

//       {/* DIVIDER */}

//       <Box
//         sx={{
//           width: "100%",
//           height: "1px",

//           backgroundColor: "#E2E8F0",

//           my: 2.25,
//         }}
//       />

//       {/* =========================
//           DETAILS GRID
//       ========================= */}

//       <Box
//         sx={{
//           display: "grid",

//           gridTemplateColumns: {
//             xs: "1fr",
//             sm: "1fr 1fr",
//           },

//           columnGap: 4,
//           rowGap: 2,
//         }}
//       >
//         <DetailItem
//           icon={<CreditCardOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Plan Type"
//           value={plan.type || "—"}
//         />

//         {/* <DetailItem
//           icon={<CalendarTodayOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Billing Cycle"
//           value={plan.billing_cycle === "yearly" ? "Yearly" : "Monthly"}
//         /> */}

//         <DetailItem
//           icon={<CreditCardOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Monthly Price"
//           value={`₹${formatPrice(monthlyPrice)}`}
//         />

//         <DetailItem
//           icon={<CreditCardOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Yearly Price"
//           value={`₹${formatPrice(yearlyPrice)}`}
//         />

//         <DetailItem
//           icon={<ShareOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Social Accounts"
//           value={limits.accounts ?? 0}
//         />

//         <DetailItem
//           icon={<EditOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Posts / Posters"
//           value={`${limits.posts ?? 0} / month`}
//         />

//         <DetailItem
//           icon={<VideoLibraryOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Videos"
//           value={`${limits.videos ?? 0} / month`}
//         />

//         <DetailItem
//           icon={<CampaignOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Ads / Campaigns"
//           value={limits.ads ?? 0}
//         />

//         <DetailItem
//           icon={<AutoAwesomeOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="DM Automations"
//           value={limits.dm_automations ?? 0}
//         />

//         <DetailItem
//           icon={<CalendarTodayOutlinedIcon sx={{ fontSize: 17 }} />}
//           label="Created"
//           value={formatDate(plan.created_at)}
//         />
//       </Box>

//       {/* =========================
//           HIGHLIGHTS DIVIDER
//       ========================= */}

//       <Box
//         sx={{
//           width: "100%",
//           height: "1px",

//           backgroundColor: "#E2E8F0",

//           my: 2.25,
//         }}
//       />

//       {/* =========================
//           PLAN HIGHLIGHTS
//       ========================= */}

//       <Typography
//         sx={{
//           fontSize: "13px",
//           fontWeight: 400,
//           lineHeight: "18px",
//           color: "#94A3B8",
//         }}
//       >
//         Plan Highlights
//       </Typography>

//       <Typography
//         sx={{
//           fontSize: "14px",
//           fontWeight: 400,
//           lineHeight: "22px",
//           color: "#475569",

//           mt: 0.75,
//         }}
//       >
//         {plan.highlights || plan.description || "—"}
//       </Typography>
//     </Paper>
//   );
// }

import { Box, Paper, Stack, Typography } from "@mui/material";

import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import VideoLibraryOutlinedIcon from "@mui/icons-material/VideoLibraryOutlined";
import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function DetailItem({ icon, label, value }) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={1.25}
      sx={{
        minWidth: 0,
      }}
    >
      <Box
        sx={{
          width: 34,
          height: 34,

          flexShrink: 0,

          display: "flex",
          alignItems: "center",
          justifyContent: "center",

          borderRadius: "9px",

          backgroundColor: "#F8FAFC",

          color: "#64748B",
        }}
      >
        {icon}
      </Box>

      <Box
        sx={{
          minWidth: 0,
        }}
      >
        <Typography
          sx={{
            fontSize: "13px",
            fontWeight: 400,
            lineHeight: "18px",
            color: "#94A3B8",
          }}
        >
          {label}
        </Typography>

        <Typography
          sx={{
            fontSize: "14px",
            fontWeight: 500,
            lineHeight: "20px",
            color: "#334155",
            mt: 0.2,

            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {value}
        </Typography>
      </Box>
    </Stack>
  );
}

export default function PlanDetailsCard({ plan }) {
  const limits = plan?.limits || {};

  const monthlyPrice = plan?.monthly_price ?? 0;

  const yearlyPrice = plan?.yearly_price ?? 0;

  return (
    <Paper
      elevation={0}
      sx={{
        width: "100%",

        p: {
          xs: 2.5,
          sm: 2.75,
        },

        borderRadius: "18px",

        border: "1px solid #E2E8F0",

        backgroundColor: "#FFFFFF",

        boxSizing: "border-box",
      }}
    >
      {/* =====================================================
          CARD TITLE
      ===================================================== */}

      <Typography
        component="h2"
        sx={{
          fontSize: "18px",
          fontWeight: 700,
          lineHeight: "24px",

          color: "#1E293B",

          m: 0,
        }}
      >
        Plan Details
      </Typography>

      {/* =====================================================
          DESCRIPTION
      ===================================================== */}

      <Typography
        sx={{
          fontSize: "14px",
          fontWeight: 400,
          lineHeight: "22px",

          color: "#475569",

          mt: 2,
        }}
      >
        {plan?.description || "—"}
      </Typography>

      {/* =====================================================
          DIVIDER
      ===================================================== */}

      <Box
        sx={{
          width: "100%",
          height: "1px",

          backgroundColor: "#E2E8F0",

          my: 2.25,
        }}
      />

      {/* =====================================================
          DETAILS GRID
      ===================================================== */}

      <Box
        sx={{
          display: "grid",

          gridTemplateColumns: {
            xs: "1fr",
            sm: "1fr 1fr",
          },

          columnGap: 4,
          rowGap: 2,
        }}
      >
        {/* PLAN TYPE */}

        <DetailItem
          icon={
            <CreditCardOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Plan Type"
          value={plan?.type || "—"}
        />

        {/* STATUS */}

        <DetailItem
          icon={
            <CalendarTodayOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Status"
          value={plan?.status === "inactive" ? "Inactive" : "Active"}
        />

        {/* MONTHLY PRICE */}

        <DetailItem
          icon={
            <CreditCardOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Monthly Price"
          value={`₹${formatPrice(monthlyPrice)}`}
        />

        {/* YEARLY PRICE */}

        <DetailItem
          icon={
            <CreditCardOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Yearly Price"
          value={`₹${formatPrice(yearlyPrice)}`}
        />

        {/* SOCIAL ACCOUNTS */}

        <DetailItem
          icon={
            <ShareOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Social Accounts"
          value={limits.accounts ?? 0}
        />

        {/* POSTS */}

        <DetailItem
          icon={
            <EditOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Posts / Posters"
          value={`${limits.posts ?? 0} / month`}
        />

        {/* VIDEOS */}

        <DetailItem
          icon={
            <VideoLibraryOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Videos"
          value={`${limits.videos ?? 0} / month`}
        />

        {/* ADS */}

        <DetailItem
          icon={
            <CampaignOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Ads / Campaigns"
          value={limits.ads ?? 0}
        />

        {/* DM AUTOMATIONS */}

        <DetailItem
          icon={
            <AutoAwesomeOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="DM Automations"
          value={limits.dm_automations ?? 0}
        />

        {/* CREATED */}

        <DetailItem
          icon={
            <CalendarTodayOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
          }
          label="Created"
          value={formatDate(plan?.created_at)}
        />
      </Box>

      {/* =====================================================
          HIGHLIGHTS DIVIDER
      ===================================================== */}

      <Box
        sx={{
          width: "100%",
          height: "1px",

          backgroundColor: "#E2E8F0",

          my: 2.25,
        }}
      />

      {/* =====================================================
          PLAN HIGHLIGHTS
      ===================================================== */}

      <Typography
        sx={{
          fontSize: "13px",
          fontWeight: 400,
          lineHeight: "18px",

          color: "#94A3B8",
        }}
      >
        Plan Highlights
      </Typography>

      <Typography
        sx={{
          fontSize: "14px",
          fontWeight: 400,
          lineHeight: "22px",

          color: "#475569",

          mt: 0.75,
        }}
      >
        {plan?.highlights || plan?.description || "—"}
      </Typography>
    </Paper>
  );
}
