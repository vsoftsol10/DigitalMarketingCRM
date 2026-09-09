// import {
//   Box,
//   Card,
//   CardContent,
//   Chip,
//   Divider,
//   Stack,
//   Typography,
// } from "@mui/material";

// import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";
// import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
// import AccessTimeOutlinedIcon from "@mui/icons-material/AccessTimeOutlined";
// import EventOutlinedIcon from "@mui/icons-material/EventOutlined";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// import SubscriptionActions from "../../subscription/SubscriptionActions";

// function formatPlan(value) {
//   if (!value) {
//     return "-";
//   }

//   return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
// }

// function formatBillingCycle(value) {
//   if (!value) {
//     return "-";
//   }

//   return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
// }

// function formatStatus(value) {
//   if (!value) {
//     return "-";
//   }

//   return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
// }

// function formatDate(value) {
//   if (!value) {
//     return "-";
//   }

//   const date = new Date(value);

//   if (Number.isNaN(date.getTime())) {
//     return "-";
//   }

//   return date.toLocaleDateString("en-US", {
//     month: "short",
//     day: "numeric",
//     year: "numeric",
//   });
// }

// function getDaysRemaining(expiryDate) {
//   if (!expiryDate) {
//     return null;
//   }

//   const expiry = new Date(`${expiryDate}T00:00:00`);

//   if (Number.isNaN(expiry.getTime())) {
//     return null;
//   }

//   const today = new Date();

//   const todayStart = new Date(
//     today.getFullYear(),
//     today.getMonth(),
//     today.getDate(),
//   );

//   const difference = expiry.getTime() - todayStart.getTime();

//   return Math.max(0, Math.ceil(difference / (1000 * 60 * 60 * 24)));
// }

// function getStatusStyles(status) {
//   switch (status) {
//     case "active":
//       return {
//         background: "#ECFDF3",
//         color: "#059669",
//         border: "#A7F3D0",
//       };

//     case "expired":
//       return {
//         background: "#FEF2F2",
//         color: "#DC2626",
//         border: "#FECACA",
//       };

//     case "cancelled":
//       return {
//         background: "#F8FAFC",
//         color: "#64748B",
//         border: "#CBD5E1",
//       };

//     default:
//       return {
//         background: "#F8FAFC",
//         color: "#64748B",
//         border: "#CBD5E1",
//       };
//   }
// }

// function DetailRow({ icon, label, value, valueColor = "#334155" }) {
//   return (
//     <Stack
//       direction="row"
//       alignItems="center"
//       sx={{
//         minWidth: 0,
//       }}
//     >
//       <Box
//         sx={{
//           width: 32,
//           height: 32,

//           borderRadius: "9px",

//           backgroundColor: "#F8FAFC",
//           color: "#94A3B8",

//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",

//           flexShrink: 0,

//           "& svg": {
//             fontSize: 17,
//           },
//         }}
//       >
//         {icon}
//       </Box>

//       <Typography
//         sx={{
//           ml: 1.25,

//           fontSize: 14,
//           lineHeight: "20px",
//           color: "#64748B",

//           flex: 1,
//           minWidth: 0,
//         }}
//       >
//         {label}
//       </Typography>

//       <Typography
//         sx={{
//           ml: 1,

//           fontSize: 14,
//           lineHeight: "20px",
//           fontWeight: 500,

//           color: valueColor,

//           textAlign: "right",

//           whiteSpace: "nowrap",
//         }}
//       >
//         {value}
//       </Typography>
//     </Stack>
//   );
// }

// function UpcomingChangeCard({ plan, billingCycle, startDate, expiryDate }) {
//   if (!plan) {
//     return null;
//   }

//   return (
//     <Box
//       sx={{
//         mt: 3,

//         p: 2,

//         borderRadius: "14px",

//         backgroundColor: "#F8FAFC",

//         border: "1px solid #E2E8F0",
//       }}
//     >
//       <Stack direction="row" alignItems="center" spacing={1}>
//         <Box
//           sx={{
//             width: 34,
//             height: 34,

//             borderRadius: "10px",

//             backgroundColor: "#EEF4FF",

//             color: "#2563EB",

//             display: "flex",
//             alignItems: "center",
//             justifyContent: "center",

//             flexShrink: 0,
//           }}
//         >
//           <EventOutlinedIcon
//             sx={{
//               fontSize: 18,
//             }}
//           />
//         </Box>

//         <Box
//           sx={{
//             minWidth: 0,
//           }}
//         >
//           <Typography
//             sx={{
//               fontSize: 12,
//               lineHeight: "18px",

//               color: "#94A3B8",

//               textTransform: "uppercase",

//               letterSpacing: "0.04em",

//               fontWeight: 600,
//             }}
//           >
//             Upcoming Change
//           </Typography>
//         </Box>
//       </Stack>

//       <Box
//         sx={{
//           mt: 2,
//         }}
//       >
//         <Typography
//           sx={{
//             fontSize: 16,
//             lineHeight: "22px",
//             fontWeight: 700,

//             color: "#0F172A",
//           }}
//         >
//           {formatPlan(plan)}
//         </Typography>

//         <Typography
//           sx={{
//             mt: 0.25,

//             fontSize: 13,
//             lineHeight: "20px",

//             color: "#64748B",
//           }}
//         >
//           {formatBillingCycle(billingCycle)}
//         </Typography>
//       </Box>

//       <Divider
//         sx={{
//           my: 2,
//         }}
//       />

//       <Stack spacing={1.5}>
//         <DetailRow
//           icon={<CalendarTodayOutlinedIcon />}
//           label="Starts"
//           value={formatDate(startDate)}
//         />

//         <DetailRow
//           icon={<CalendarTodayOutlinedIcon />}
//           label="Expires"
//           value={formatDate(expiryDate)}
//         />
//       </Stack>
//     </Box>
//   );
// }

// export default function SubscriptionCard({
//   organization,
//   onRenew,
//   onChangePlan,
//   onCancel,
//   onStartSubscription,
//   onViewHistory,
//   actionLoading = false,
// }) {
//   if (!organization) {
//     return null;
//   }

//   // ============================================================
//   // CURRENT SUBSCRIPTION
//   // ============================================================

//   const subscriptionStatus = organization.subscription_status;

//   const hasCurrentSubscription = Boolean(subscriptionStatus);

//   const isActive = subscriptionStatus === "active";

//   const subscriptionPlan = organization.subscription_plan;

//   const billingCycle = organization.billing_cycle;

//   const subscriptionStart = organization.subscription_start;

//   const subscriptionExpiry = organization.subscription_expiry;

//   const daysRemaining = isActive ? getDaysRemaining(subscriptionExpiry) : null;

//   const statusStyles = getStatusStyles(subscriptionStatus);

//   // ============================================================
//   // UPCOMING SUBSCRIPTION
//   // ============================================================

//   const upcomingPlan = organization.upcoming_plan;

//   const upcomingBillingCycle = organization.upcoming_billing_cycle;

//   const upcomingStart = organization.upcoming_start;

//   const upcomingExpiry = organization.upcoming_expiry;

//   const hasUpcomingChange = Boolean(upcomingPlan);

//   return (
//     <Card
//       elevation={0}
//       sx={{
//         width: "100%",

//         border: "1px solid #E2E8F0",

//         borderRadius: "20px",

//         backgroundColor: "#FFFFFF",

//         boxSizing: "border-box",
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
//             TITLE
//         ================================================== */}

//         <Typography
//           sx={{
//             ...TYPOGRAPHY.sectionTitle,

//             color: "#0F172A",
//           }}
//         >
//           Subscription
//         </Typography>

//         {/* ==================================================
//             CURRENT SUBSCRIPTION
//         ================================================== */}

//         {hasCurrentSubscription ? (
//           <>
//             <Stack
//               direction="row"
//               spacing={2}
//               alignItems="center"
//               sx={{
//                 mt: 3,
//               }}
//             >
//               <Box
//                 sx={{
//                   width: 48,
//                   height: 48,

//                   borderRadius: "14px",

//                   backgroundColor: "#EEF4FF",

//                   display: "flex",
//                   alignItems: "center",
//                   justifyContent: "center",

//                   flexShrink: 0,
//                 }}
//               >
//                 <CreditCardOutlinedIcon
//                   sx={{
//                     color: "#2563EB",
//                     fontSize: 22,
//                   }}
//                 />
//               </Box>

//               <Box
//                 sx={{
//                   minWidth: 0,
//                   flex: 1,
//                 }}
//               >
//                 <Typography
//                   sx={{
//                     fontSize: 18,
//                     lineHeight: "24px",

//                     fontWeight: 700,

//                     color: "#0F172A",

//                     overflow: "hidden",

//                     textOverflow: "ellipsis",

//                     whiteSpace: "nowrap",
//                   }}
//                 >
//                   {formatPlan(subscriptionPlan)}
//                 </Typography>

//                 <Typography
//                   sx={{
//                     mt: 0.35,

//                     fontSize: 14,
//                     lineHeight: "20px",

//                     color: "#64748B",
//                   }}
//                 >
//                   {formatBillingCycle(billingCycle)}
//                 </Typography>
//               </Box>
//             </Stack>

//             <Divider
//               sx={{
//                 my: 3,
//               }}
//             />

//             {/* ==================================================
//                 STATUS
//             ================================================== */}

//             <Box>
//               <Typography
//                 sx={{
//                   fontSize: 12,
//                   lineHeight: "18px",

//                   fontWeight: 600,

//                   color: "#94A3B8",

//                   textTransform: "uppercase",

//                   letterSpacing: "0.04em",
//                 }}
//               >
//                 Subscription Status
//               </Typography>

//               <Chip
//                 label={formatStatus(subscriptionStatus)}
//                 size="small"
//                 sx={{
//                   mt: 0.75,

//                   height: 30,

//                   borderRadius: "999px",

//                   backgroundColor: statusStyles.background,

//                   color: statusStyles.color,

//                   border: "1px solid",

//                   borderColor: statusStyles.border,

//                   fontSize: 13,

//                   fontWeight: 600,

//                   "& .MuiChip-label": {
//                     px: 1.25,
//                   },
//                 }}
//               />
//             </Box>

//             <Divider
//               sx={{
//                 my: 3,
//               }}
//             />

//             {/* ==================================================
//                 SUBSCRIPTION DATES
//             ================================================== */}

//             <Stack spacing={2.2}>
//               <DetailRow
//                 icon={<CalendarTodayOutlinedIcon />}
//                 label="Start Date"
//                 value={formatDate(subscriptionStart)}
//               />

//               <DetailRow
//                 icon={<CalendarTodayOutlinedIcon />}
//                 label="Expiry Date"
//                 value={formatDate(subscriptionExpiry)}
//                 valueColor={
//                   subscriptionStatus === "expired" ? "#DC2626" : "#334155"
//                 }
//               />

//               {isActive && daysRemaining !== null && (
//                 <DetailRow
//                   icon={<AccessTimeOutlinedIcon />}
//                   label="Days Remaining"
//                   value={`${daysRemaining} ${
//                     daysRemaining === 1 ? "day" : "days"
//                   }`}
//                   valueColor={daysRemaining <= 7 ? "#DC2626" : "#334155"}
//                 />
//               )}
//             </Stack>

//             {/* ==================================================
//                 UPCOMING CHANGE
//             ================================================== */}

//             {hasUpcomingChange && (
//               <UpcomingChangeCard
//                 plan={upcomingPlan}
//                 billingCycle={upcomingBillingCycle}
//                 startDate={upcomingStart}
//                 expiryDate={upcomingExpiry}
//               />
//             )}
//           </>
//         ) : (
//           <>
//             {/* ==================================================
//                 NO CURRENT SUBSCRIPTION
//             ================================================== */}

//             <Box
//               sx={{
//                 mt: 3,

//                 p: 2.5,

//                 borderRadius: "14px",

//                 backgroundColor: "#F8FAFC",

//                 border: "1px dashed #CBD5E1",
//               }}
//             >
//               <Typography
//                 sx={{
//                   fontSize: 14,
//                   fontWeight: 600,

//                   color: "#334155",
//                 }}
//               >
//                 No current subscription
//               </Typography>

//               <Typography
//                 sx={{
//                   mt: 0.5,

//                   fontSize: 13,
//                   lineHeight: "20px",

//                   color: "#64748B",
//                 }}
//               >
//                 This organization does not currently have an active
//                 subscription.
//               </Typography>
//             </Box>
//           </>
//         )}

//         {/* ==================================================
//             ACTIONS
//         ================================================== */}

//         <SubscriptionActions
//           hasCurrentSubscription={hasCurrentSubscription}
//           isActive={isActive}
//           hasUpcomingSubscription={hasUpcomingChange}
//           onRenew={onRenew}
//           onChangePlan={onChangePlan}
//           onCancel={onCancel}
//           onStart={onStartSubscription}
//           loading={actionLoading}
//         />

//         <Box
//           sx={{
//             mt: 2.5,
//             pt: 2,
//             borderTop: "1px solid #E2E8F0",
//           }}
//         >
//           <Typography
//             component="button"
//             type="button"
//             onClick={onViewHistory}
//             disabled={!onViewHistory}
//             sx={{
//               p: 0,
//               border: 0,
//               background: "transparent",

//               color: "#2563EB",

//               fontSize: 13,
//               fontWeight: 600,

//               cursor: onViewHistory ? "pointer" : "default",

//               "&:hover": {
//                 textDecoration: onViewHistory ? "underline" : "none",
//               },
//             }}
//           >
//             View Subscription History →
//           </Typography>
//         </Box>
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

import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";
import CalendarTodayOutlinedIcon from "@mui/icons-material/CalendarTodayOutlined";
import AccessTimeOutlinedIcon from "@mui/icons-material/AccessTimeOutlined";
import EventOutlinedIcon from "@mui/icons-material/EventOutlined";

import { TYPOGRAPHY } from "../../../../theme/typography";

import SubscriptionActions from "../../subscription/SubscriptionActions";

// ============================================================
// FORMATTERS
// ============================================================

function formatPlan(value) {
  if (!value) {
    return "-";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function formatBillingCycle(value) {
  if (!value) {
    return "-";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function formatStatus(value) {
  if (!value) {
    return "-";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

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

// ============================================================
// DATE HELPERS
// ============================================================

function getDaysRemaining(expiryDate) {
  if (!expiryDate) {
    return null;
  }

  const expiry = new Date(`${expiryDate}T00:00:00`);

  if (Number.isNaN(expiry.getTime())) {
    return null;
  }

  const today = new Date();

  const todayStart = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  );

  const difference = expiry.getTime() - todayStart.getTime();

  return Math.max(0, Math.ceil(difference / (1000 * 60 * 60 * 24)));
}

// ============================================================
// STATUS STYLES
// ============================================================

function getStatusStyles(status) {
  switch (status) {
    case "active":
      return {
        background: "#ECFDF3",
        color: "#059669",
        border: "#A7F3D0",
      };

    case "expired":
      return {
        background: "#FEF2F2",
        color: "#DC2626",
        border: "#FECACA",
      };

    case "cancelled":
      return {
        background: "#F8FAFC",
        color: "#64748B",
        border: "#CBD5E1",
      };

    default:
      return {
        background: "#F8FAFC",
        color: "#64748B",
        border: "#CBD5E1",
      };
  }
}

// ============================================================
// DETAIL ROW
// ============================================================

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
          whiteSpace: "nowrap",
        }}
      >
        {value}
      </Typography>
    </Stack>
  );
}

// ============================================================
// UPCOMING CHANGE CARD
// ============================================================

function UpcomingChangeCard({ plan, billingCycle, startDate, expiryDate }) {
  if (!plan) {
    return null;
  }

  return (
    <Box
      sx={{
        mt: 3,
        p: 2,
        borderRadius: "14px",
        backgroundColor: "#F8FAFC",
        border: "1px solid #E2E8F0",
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        <Box
          sx={{
            width: 34,
            height: 34,
            borderRadius: "10px",
            backgroundColor: "#EEF4FF",
            color: "#2563EB",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <EventOutlinedIcon
            sx={{
              fontSize: 18,
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
              fontSize: 12,
              lineHeight: "18px",
              color: "#94A3B8",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              fontWeight: 600,
            }}
          >
            Upcoming Change
          </Typography>
        </Box>
      </Stack>

      <Box
        sx={{
          mt: 2,
        }}
      >
        <Typography
          sx={{
            fontSize: 16,
            lineHeight: "22px",
            fontWeight: 700,
            color: "#0F172A",
          }}
        >
          {formatPlan(plan)}
        </Typography>

        <Typography
          sx={{
            mt: 0.25,
            fontSize: 13,
            lineHeight: "20px",
            color: "#64748B",
          }}
        >
          {formatBillingCycle(billingCycle)}
        </Typography>
      </Box>

      <Divider
        sx={{
          my: 2,
        }}
      />

      <Stack spacing={1.5}>
        <DetailRow
          icon={<CalendarTodayOutlinedIcon />}
          label="Starts"
          value={formatDate(startDate)}
        />

        <DetailRow
          icon={<CalendarTodayOutlinedIcon />}
          label="Expires"
          value={formatDate(expiryDate)}
        />
      </Stack>
    </Box>
  );
}

// ============================================================
// EXPIRED SUBSCRIPTION CARD
// ============================================================

function ExpiredSubscriptionCard({ status, plan, billingCycle, expiryDate }) {
  return (
    <Box
      sx={{
        mt: 3,
        p: 2.5,
        borderRadius: "14px",
        backgroundColor: "#F8FAFC",
        border: "1px dashed #CBD5E1",
      }}
    >
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
        Subscription Status
      </Typography>

      <Chip
        label={formatStatus(status)}
        size="small"
        sx={{
          mt: 0.75,
          height: 30,
          borderRadius: "999px",
          backgroundColor: "#FEF2F2",
          color: "#DC2626",
          border: "1px solid #FECACA",
          fontSize: 13,
          fontWeight: 600,

          "& .MuiChip-label": {
            px: 1.25,
          },
        }}
      />

      {plan && (
        <>
          <Typography
            sx={{
              mt: 2.5,
              fontSize: 12,
              color: "#94A3B8",
              textTransform: "uppercase",
              fontWeight: 600,
              letterSpacing: "0.04em",
            }}
          >
            Previous Plan
          </Typography>

          <Typography
            sx={{
              mt: 0.5,
              fontSize: 17,
              fontWeight: 700,
              color: "#0F172A",
            }}
          >
            {formatPlan(plan)}
          </Typography>

          {billingCycle && (
            <Typography
              sx={{
                mt: 0.25,
                fontSize: 13,
                color: "#64748B",
                textTransform: "capitalize",
              }}
            >
              {formatBillingCycle(billingCycle)}
            </Typography>
          )}
        </>
      )}

      {expiryDate && (
        <>
          <Divider
            sx={{
              my: 2.5,
            }}
          />

          <DetailRow
            icon={<CalendarTodayOutlinedIcon />}
            label="Expired On"
            value={formatDate(expiryDate)}
            valueColor="#DC2626"
          />
        </>
      )}

      {!plan && !expiryDate && (
        <Typography
          sx={{
            mt: 0.75,
            fontSize: 13,
            lineHeight: "20px",
            color: "#64748B",
          }}
        >
          This organization does not currently have an active subscription.
        </Typography>
      )}
    </Box>
  );
}

// ============================================================
// COMPONENT
// ============================================================

export default function SubscriptionCard({
  organization,
  onRenew,
  onChangePlan,
  onCancel,
  onStartSubscription,
  onViewHistory,
  actionLoading = false,
}) {
  if (!organization) {
    return null;
  }

  // ============================================================
  // CURRENT SUBSCRIPTION
  // ============================================================

  const subscriptionStatus = organization.subscription_status || null;

  const hasCurrentSubscription = Boolean(subscriptionStatus);

  const isActive = subscriptionStatus === "active";

  // ============================================================
  // PREVIOUS SUBSCRIPTION
  // ============================================================

  const lastSubscriptionStatus = organization.last_subscription_status || null;

  const lastSubscriptionPlan = organization.last_subscription_plan || null;

  const lastSubscriptionBillingCycle =
    organization.last_subscription_billing_cycle || null;

  const lastSubscriptionExpiry = organization.last_subscription_expiry || null;

  const displaySubscriptionStatus =
    subscriptionStatus || lastSubscriptionStatus;

  // ============================================================
  // CURRENT PLAN DETAILS
  // ============================================================

  const subscriptionPlan = organization.subscription_plan;

  const billingCycle = organization.billing_cycle;

  const subscriptionStart = organization.subscription_start;

  const subscriptionExpiry = organization.subscription_expiry;

  const daysRemaining = isActive ? getDaysRemaining(subscriptionExpiry) : null;

  const statusStyles = getStatusStyles(displaySubscriptionStatus);

  // ============================================================
  // UPCOMING SUBSCRIPTION
  // ============================================================

  const upcomingPlan = organization.upcoming_plan;

  const upcomingBillingCycle = organization.upcoming_billing_cycle;

  const upcomingStart = organization.upcoming_start;

  const upcomingExpiry = organization.upcoming_expiry;

  const hasUpcomingChange = Boolean(upcomingPlan);

  // ============================================================
  // RENDER
  // ============================================================

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
          Subscription
        </Typography>

        {/* ==================================================
            CURRENT SUBSCRIPTION
        ================================================== */}

        {hasCurrentSubscription ? (
          <>
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
                  backgroundColor: "#EEF4FF",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <CreditCardOutlinedIcon
                  sx={{
                    color: "#2563EB",
                    fontSize: 22,
                  }}
                />
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
                  {formatPlan(subscriptionPlan)}
                </Typography>

                <Typography
                  sx={{
                    mt: 0.35,
                    fontSize: 14,
                    lineHeight: "20px",
                    color: "#64748B",
                  }}
                >
                  {formatBillingCycle(billingCycle)}
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
                Subscription Status
              </Typography>

              <Chip
                label={formatStatus(subscriptionStatus)}
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
                SUBSCRIPTION DATES
            ================================================== */}

            <Stack spacing={2.2}>
              <DetailRow
                icon={<CalendarTodayOutlinedIcon />}
                label="Start Date"
                value={formatDate(subscriptionStart)}
              />

              <DetailRow
                icon={<CalendarTodayOutlinedIcon />}
                label="Expiry Date"
                value={formatDate(subscriptionExpiry)}
                valueColor={
                  subscriptionStatus === "expired" ? "#DC2626" : "#334155"
                }
              />

              {isActive && daysRemaining !== null && (
                <DetailRow
                  icon={<AccessTimeOutlinedIcon />}
                  label="Days Remaining"
                  value={`${daysRemaining} ${
                    daysRemaining === 1 ? "day" : "days"
                  }`}
                  valueColor={daysRemaining <= 7 ? "#DC2626" : "#334155"}
                />
              )}
            </Stack>

            {/* ==================================================
                UPCOMING CHANGE
            ================================================== */}

            {hasUpcomingChange && (
              <UpcomingChangeCard
                plan={upcomingPlan}
                billingCycle={upcomingBillingCycle}
                startDate={upcomingStart}
                expiryDate={upcomingExpiry}
              />
            )}
          </>
        ) : (
          <>
            {/* ==================================================
                NO CURRENT / EXPIRED SUBSCRIPTION
            ================================================== */}

            <ExpiredSubscriptionCard
              status={displaySubscriptionStatus || "none"}
              plan={lastSubscriptionPlan}
              billingCycle={lastSubscriptionBillingCycle}
              expiryDate={lastSubscriptionExpiry}
            />
          </>
        )}

        {/* ==================================================
            ACTIONS
        ================================================== */}

        <SubscriptionActions
          hasCurrentSubscription={hasCurrentSubscription}
          isActive={isActive}
          subscriptionStatus={displaySubscriptionStatus}
          lastSubscriptionExpiry={lastSubscriptionExpiry}
          hasUpcomingSubscription={hasUpcomingChange}
          onRenew={onRenew}
          onChangePlan={onChangePlan}
          onCancel={onCancel}
          onStart={onStartSubscription}
          loading={actionLoading}
        />

        {/* ==================================================
            HISTORY
        ================================================== */}

        <Box
          sx={{
            mt: 2.5,
            pt: 2,
            borderTop: "1px solid #E2E8F0",
          }}
        >
          <Typography
            component="button"
            type="button"
            onClick={onViewHistory}
            disabled={!onViewHistory}
            sx={{
              p: 0,
              border: 0,
              background: "transparent",
              color: "#2563EB",
              fontSize: 13,
              fontWeight: 600,
              cursor: onViewHistory ? "pointer" : "default",

              "&:hover": {
                textDecoration: onViewHistory ? "underline" : "none",
              },
            }}
          >
            View Subscription History →
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}
