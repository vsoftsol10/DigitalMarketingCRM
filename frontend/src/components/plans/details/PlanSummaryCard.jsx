// import { Box, Chip, Paper, Stack, Typography } from "@mui/material";

// import CheckIcon from "@mui/icons-material/Check";

// function formatPrice(value) {
//   return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
// }

// function FeatureItem({ children }) {
//   return (
//     <Stack
//       direction="row"
//       alignItems="center"
//       spacing={1}
//       sx={{
//         minWidth: 0,
//       }}
//     >
//       <CheckIcon
//         sx={{
//           fontSize: 17,
//           color: "#10B981",
//           flexShrink: 0,
//         }}
//       />

//       <Typography
//         sx={{
//           fontSize: "14px",
//           fontWeight: 400,
//           lineHeight: "21px",
//           color: "#475569",
//         }}
//       >
//         {children}
//       </Typography>
//     </Stack>
//   );
// }

// export default function PlanSummaryCard({ plan }) {
//   // const price =
//   //   plan.billing_cycle === "yearly"
//   //     ? plan.yearly_price
//   //     : plan.monthly_price;

//   const limits = plan.limits || {};

//   const isInactive = plan.status === "inactive";

//   return (
//     <Box
//       sx={{
//         position: {
//           xs: "static",
//           md: "sticky",
//         },

//         top: 24,

//         width: "100%",
//       }}
//     >
//       <Paper
//         elevation={0}
//         sx={{
//           width: "100%",

//           p: {
//             xs: 2.5,
//             sm: 2.75,
//           },

//           borderRadius: "18px",

//           border: "1px solid #DBE5F5",

//           backgroundColor: "#FFFFFF",

//           boxSizing: "border-box",
//         }}
//       >
//         {/* =========================
//             PLAN TYPE
//         ========================= */}

//         <Typography
//           align="center"
//           sx={{
//             fontSize: "12px",
//             fontWeight: 500,
//             lineHeight: "18px",

//             color: "#94A3B8",

//             textTransform: "uppercase",

//             letterSpacing: "0.04em",
//           }}
//         >
//           {(plan.type || "Basic").toUpperCase()}
//         </Typography>

//         {/* =========================
//             PLAN NAME
//         ========================= */}

//         <Typography
//           align="center"
//           sx={{
//             fontSize: "27px",
//             fontWeight: 700,
//             lineHeight: "34px",

//             letterSpacing: "-0.02em",

//             color: "#1E293B",

//             mt: 0.45,
//           }}
//         >
//           {plan.name || "Plan Name"}
//         </Typography>

//         {/* =========================
//             DESCRIPTION
//         ========================= */}

//         <Typography
//           align="center"
//           sx={{
//             fontSize: "14px",
//             fontWeight: 400,
//             lineHeight: "21px",

//             color: "#64748B",

//             mt: 0.5,

//             minHeight: 63,
//           }}
//         >
//           {plan.description || "Plan description"}
//         </Typography>

//         {/* =========================
//             PRICE
//         ========================= */}

//         {/* <Stack
//           direction="row"
//           alignItems="baseline"
//           justifyContent="center"
//           spacing={0.35}
//           sx={{
//             mt: 1.75,
//           }}
//         >
//           <Typography
//             sx={{
//               fontSize: "26px",
//               fontWeight: 700,
//               lineHeight: "32px",

//               letterSpacing: "-0.02em",

//               color: "#2563EB",
//             }}
//           >
//             ₹{formatPrice(price)}
//           </Typography>

//           <Typography
//             sx={{
//               fontSize: "13px",
//               fontWeight: 400,
//               lineHeight: "20px",

//               color: "#94A3B8",
//             }}
//           >
//             /{" "}
//             {plan.billing_cycle === "yearly"
//               ? "year"
//               : "month"}
//           </Typography>
//         </Stack> */}
//         <Stack direction="row" justifyContent="center" spacing={3}>
//           <Box>
//             <Typography>₹{formatPrice(plan.monthly_price)}</Typography>

//             <Typography>/ month</Typography>
//           </Box>

//           <Box>
//             <Typography>₹{formatPrice(plan.yearly_price)}</Typography>

//             <Typography>/ year</Typography>
//           </Box>
//         </Stack>

//         {/* =========================
//             DIVIDER
//         ========================= */}

//         <Box
//           sx={{
//             width: "100%",
//             height: "1px",

//             backgroundColor: "#E2E8F0",

//             my: 2.25,
//           }}
//         />

//         {/* =========================
//             PLAN LIMITS
//         ========================= */}

//         <Stack
//           spacing={1.05}
//           sx={{
//             textAlign: "left",
//           }}
//         >
//           <FeatureItem>{limits.accounts ?? 0} Social Accounts</FeatureItem>

//           <FeatureItem>
//             {limits.posts ?? 0} Posts / Posters per month
//           </FeatureItem>

//           <FeatureItem>{limits.videos ?? 0} Videos per month</FeatureItem>

//           <FeatureItem>{limits.ads ?? 0} Ads / Campaigns</FeatureItem>

//           <FeatureItem>{limits.dm_automations ?? 0} DM Automations</FeatureItem>
//         </Stack>

//         {/* =========================
//             STATUS
//         ========================= */}

//         <Chip
//           label={isInactive ? "Inactive" : "Active"}
//           size="small"
//           sx={{
//             mt: 2.5,

//             height: 28,

//             border: "1px solid",

//             borderColor: isInactive ? "#CBD5E1" : "#86EFAC",

//             backgroundColor: isInactive ? "#F8FAFC" : "#F0FDF4",

//             color: isInactive ? "#64748B" : "#059669",

//             fontSize: "12px",
//             fontWeight: 500,

//             "& .MuiChip-label": {
//               px: 1.2,
//             },
//           }}
//         />
//       </Paper>
//     </Box>
//   );
// }

import { Box, Chip, Paper, Stack, Typography } from "@mui/material";

import CheckIcon from "@mui/icons-material/Check";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

function FeatureItem({ children }) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={1}
      sx={{
        minWidth: 0,
      }}
    >
      <CheckIcon
        sx={{
          fontSize: 17,
          color: "#10B981",
          flexShrink: 0,
        }}
      />

      <Typography
        sx={{
          fontSize: "14px",
          fontWeight: 400,
          lineHeight: "21px",
          color: "#475569",
        }}
      >
        {children}
      </Typography>
    </Stack>
  );
}

function PriceBlock({ label, value }) {
  return (
    <Box
      sx={{
        flex: 1,
        textAlign: "center",
      }}
    >
      <Typography
        sx={{
          fontSize: "12px",
          fontWeight: 500,
          lineHeight: "18px",

          color: "#94A3B8",

          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        {label}
      </Typography>

      <Typography
        sx={{
          mt: 0.35,

          fontSize: "24px",
          fontWeight: 700,
          lineHeight: "32px",

          color: "#2563EB",

          whiteSpace: "nowrap",
        }}
      >
        ₹{formatPrice(value)}
      </Typography>
    </Box>
  );
}

export default function PlanSummaryCard({ plan }) {
  const limits = plan?.limits || {};

  const isInactive = plan?.status === "inactive";

  return (
    <Box
      sx={{
        position: {
          xs: "static",
          md: "sticky",
        },

        top: 24,

        width: "100%",
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: "100%",

          p: {
            xs: 2.5,
            sm: 2.75,
          },

          borderRadius: "18px",

          border: "1px solid #DBE5F5",

          backgroundColor: "#FFFFFF",

          boxSizing: "border-box",
        }}
      >
        {/* ===================================================
            PLAN TYPE
        =================================================== */}

        <Typography
          align="center"
          sx={{
            fontSize: "12px",
            fontWeight: 500,
            lineHeight: "18px",

            color: "#94A3B8",

            textTransform: "uppercase",

            letterSpacing: "0.04em",
          }}
        >
          {(plan?.type || "Plan").toUpperCase()}
        </Typography>

        {/* ===================================================
            PLAN NAME
        =================================================== */}

        <Typography
          align="center"
          sx={{
            fontSize: "27px",
            fontWeight: 700,
            lineHeight: "34px",

            letterSpacing: "-0.02em",

            color: "#1E293B",

            mt: 0.45,

            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {plan?.name || "Plan Name"}
        </Typography>

        {/* ===================================================
            DESCRIPTION
        =================================================== */}

        <Typography
          align="center"
          sx={{
            fontSize: "14px",
            fontWeight: 400,
            lineHeight: "21px",

            color: "#64748B",

            mt: 0.5,

            minHeight: 63,

            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {plan?.description || "Plan description"}
        </Typography>

        {/* ===================================================
            PRICING
        =================================================== */}

        <Stack
          direction="row"
          spacing={1.5}
          sx={{
            mt: 2,

            p: 1.5,

            borderRadius: "14px",

            backgroundColor: "#F8FAFC",

            border: "1px solid #E2E8F0",
          }}
        >
          <PriceBlock label="Monthly" value={plan?.monthly_price} />

          <Box
            sx={{
              width: "1px",
              backgroundColor: "#E2E8F0",
            }}
          />

          <PriceBlock label="Yearly" value={plan?.yearly_price} />
        </Stack>

        {/* ===================================================
            DIVIDER
        =================================================== */}

        <Box
          sx={{
            width: "100%",
            height: "1px",

            backgroundColor: "#E2E8F0",

            my: 2.25,
          }}
        />

        {/* ===================================================
            LIMITS
        =================================================== */}

        <Stack
          spacing={1.05}
          sx={{
            textAlign: "left",
          }}
        >
          <FeatureItem>{limits.accounts ?? 0} Social Accounts</FeatureItem>

          <FeatureItem>
            {limits.posts ?? 0} Posts / Posters per month
          </FeatureItem>

          <FeatureItem>{limits.videos ?? 0} Videos per month</FeatureItem>

          <FeatureItem>{limits.ads ?? 0} Ads / Campaigns</FeatureItem>

          <FeatureItem>{limits.dm_automations ?? 0} DM Automations</FeatureItem>
        </Stack>

        {/* ===================================================
            STATUS
        =================================================== */}

        <Chip
          label={isInactive ? "Inactive" : "Active"}
          size="small"
          sx={{
            mt: 2.5,

            height: 28,

            border: "1px solid",

            borderColor: isInactive ? "#CBD5E1" : "#86EFAC",

            backgroundColor: isInactive ? "#F8FAFC" : "#F0FDF4",

            color: isInactive ? "#64748B" : "#059669",

            fontSize: "12px",
            fontWeight: 500,

            "& .MuiChip-label": {
              px: 1.2,
            },
          }}
        />
      </Paper>
    </Box>
  );
}
