// import { Box, Button, Stack } from "@mui/material";

// export default function SubscriptionActions({
//   hasCurrentSubscription,
//   isActive,
//   hasUpcomingSubscription,
//   onRenew,
//   onChangePlan,
//   onCancel,
//   onStart,
//   loading = false,
// }) {
//   if (!hasCurrentSubscription) {
//     return (
//       <Box
//         sx={{
//           mt: 3,
//         }}
//       >
//         <Button
//           fullWidth
//           variant="contained"
//           onClick={onStart}
//           disabled={loading || !onStart}
//           sx={{
//             minHeight: 42,
//             borderRadius: "12px",

//             textTransform: "none",

//             fontSize: 14,
//             fontWeight: 600,

//             boxShadow: "none",

//             "&:hover": {
//               boxShadow: "none",
//             },
//           }}
//         >
//           Start Subscription
//         </Button>
//       </Box>
//     );
//   }

//   if (!isActive) {
//     return null;
//   }

//   return (
//     <Stack
//       spacing={1}
//       sx={{
//         mt: 3,
//       }}
//     >
//       <Button
//         fullWidth
//         variant="contained"
//         onClick={onRenew}
//         disabled={loading || !onRenew || hasUpcomingSubscription}
//         sx={{
//           minHeight: 42,
//           borderRadius: "12px",

//           textTransform: "none",

//           fontSize: 14,
//           fontWeight: 600,

//           boxShadow: "none",

//           "&:hover": {
//             boxShadow: "none",
//           },
//         }}
//       >
//         {hasUpcomingSubscription ? "Renew Scheduled" : "Renew Subscription"}
//       </Button>

//       <Button
//         fullWidth
//         variant="outlined"
//         onClick={onChangePlan}
//         disabled={loading || !onChangePlan || hasUpcomingSubscription}
//         sx={{
//           minHeight: 42,
//           borderRadius: "12px",

//           textTransform: "none",

//           fontSize: 14,
//           fontWeight: 600,

//           borderColor: "#CBD5E1",

//           color: "#475569",

//           "&:hover": {
//             borderColor: "#94A3B8",
//             backgroundColor: "#F8FAFC",
//           },
//         }}
//       >
//         {hasUpcomingSubscription ? "Plan Change Scheduled" : "Change Plan"}
//       </Button>

//       <Button
//         fullWidth
//         variant="text"
//         color="error"
//         onClick={onCancel}
//         disabled={loading || !onCancel}
//         sx={{
//           minHeight: 38,
//           borderRadius: "12px",

//           textTransform: "none",

//           fontSize: 14,
//           fontWeight: 500,
//         }}
//       >
//         Cancel Subscription
//       </Button>
//     </Stack>
//   );
// }

import { Box, Button, Stack } from "@mui/material";

const EXPIRY_GRACE_PERIOD_DAYS = 20;

function getDaysSinceExpiry(expiryDate) {
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

  const expiryStart = new Date(
    expiry.getFullYear(),
    expiry.getMonth(),
    expiry.getDate(),
  );

  const difference = todayStart.getTime() - expiryStart.getTime();

  return Math.floor(difference / (1000 * 60 * 60 * 24));
}

export default function SubscriptionActions({
  hasCurrentSubscription,
  isActive,
  subscriptionStatus,
  lastSubscriptionExpiry,
  hasUpcomingSubscription,
  onRenew,
  onChangePlan,
  onCancel,
  onStart,
  loading = false,
}) {
  // ============================================================
  // ACTIVE SUBSCRIPTION
  // ============================================================

  if (hasCurrentSubscription && isActive) {
    return (
      <Stack
        spacing={1}
        sx={{
          mt: 3,
        }}
      >
        <Button
          fullWidth
          variant="contained"
          onClick={onRenew}
          disabled={loading || !onRenew || hasUpcomingSubscription}
          sx={{
            minHeight: 42,
            borderRadius: "12px",
            textTransform: "none",
            fontSize: 14,
            fontWeight: 600,
            boxShadow: "none",

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          {hasUpcomingSubscription ? "Renew Scheduled" : "Renew Subscription"}
        </Button>

        <Button
          fullWidth
          variant="outlined"
          onClick={onChangePlan}
          disabled={loading || !onChangePlan || hasUpcomingSubscription}
          sx={{
            minHeight: 42,
            borderRadius: "12px",
            textTransform: "none",
            fontSize: 14,
            fontWeight: 600,
            borderColor: "#CBD5E1",
            color: "#475569",

            "&:hover": {
              borderColor: "#94A3B8",
              backgroundColor: "#F8FAFC",
            },
          }}
        >
          {hasUpcomingSubscription ? "Plan Change Scheduled" : "Change Plan"}
        </Button>

        <Button
          fullWidth
          variant="text"
          color="error"
          onClick={onCancel}
          disabled={loading || !onCancel}
          sx={{
            minHeight: 38,
            borderRadius: "12px",
            textTransform: "none",
            fontSize: 14,
            fontWeight: 500,
          }}
        >
          Cancel Subscription
        </Button>
      </Stack>
    );
  }

  // ============================================================
  // EXPIRED SUBSCRIPTION
  // ============================================================

  const isExpired = subscriptionStatus === "expired";

  const daysSinceExpiry = isExpired
    ? getDaysSinceExpiry(lastSubscriptionExpiry)
    : null;

  const canRenewExpiredSubscription =
    isExpired &&
    daysSinceExpiry !== null &&
    daysSinceExpiry >= 0 &&
    daysSinceExpiry <= EXPIRY_GRACE_PERIOD_DAYS;

  // ============================================================
  // EXPIRED - WITHIN 20 DAYS
  // ============================================================

  if (canRenewExpiredSubscription) {
    return (
      <Stack
        spacing={1}
        sx={{
          mt: 3,
        }}
      >
        <Button
          fullWidth
          variant="contained"
          onClick={onRenew}
          disabled={loading || !onRenew}
          sx={{
            minHeight: 42,
            borderRadius: "12px",
            textTransform: "none",
            fontSize: 14,
            fontWeight: 600,
            boxShadow: "none",

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          Renew Subscription
        </Button>

        <Button
          fullWidth
          variant="outlined"
          onClick={onStart}
          disabled={loading || !onStart}
          sx={{
            minHeight: 42,
            borderRadius: "12px",
            textTransform: "none",
            fontSize: 14,
            fontWeight: 600,
            borderColor: "#CBD5E1",
            color: "#475569",

            "&:hover": {
              borderColor: "#94A3B8",
              backgroundColor: "#F8FAFC",
            },
          }}
        >
          Start Subscription
        </Button>
      </Stack>
    );
  }

  // ============================================================
  // EXPIRED - MORE THAN 20 DAYS
  // ============================================================

  if (isExpired) {
    return (
      <Box
        sx={{
          mt: 3,
        }}
      >
        <Button
          fullWidth
          variant="contained"
          onClick={onStart}
          disabled={loading || !onStart}
          sx={{
            minHeight: 42,
            borderRadius: "12px",
            textTransform: "none",
            fontSize: 14,
            fontWeight: 600,
            boxShadow: "none",

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          Start Subscription
        </Button>
      </Box>
    );
  }

  // ============================================================
  // CANCELLED / NO CURRENT SUBSCRIPTION
  // ============================================================

  return (
    <Box
      sx={{
        mt: 3,
      }}
    >
      <Button
        fullWidth
        variant="contained"
        onClick={onStart}
        disabled={loading || !onStart}
        sx={{
          minHeight: 42,
          borderRadius: "12px",
          textTransform: "none",
          fontSize: 14,
          fontWeight: 600,
          boxShadow: "none",

          "&:hover": {
            boxShadow: "none",
          },
        }}
      >
        Start Subscription
      </Button>
    </Box>
  );
}
