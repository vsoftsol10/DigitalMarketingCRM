// import { Grid } from "@mui/material";

// import OrganizationCard from "./OrganizationCard";

// export default function OrganizationGrid({
//   organizations = [],
//   onOrganizationClick,
// }) {
//   return (
//     <Grid container spacing={3}>
//       {organizations.map((organization) => (
//         <Grid
//           key={organization.id}
//           size={{
//             xs: 12,
//             md: 6,
//             xl: 4,
//           }}
//         >
//           <OrganizationCard
//             organization={organization}
//             onClick={() => onOrganizationClick?.(organization)}
//           />
//         </Grid>
//       ))}
//     </Grid>
//   );
// }

import { Box, CircularProgress, Grid } from "@mui/material";

import OrganizationCard from "./OrganizationCard";

export default function OrganizationGrid({
  organizations = [],
  onOrganizationClick,
  loading = false,
}) {
  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        minHeight: organizations.length > 0 ? undefined : 280,
      }}
    >
      {/* =====================================================
          CONTENT
      ===================================================== */}

      <Grid container spacing={3}>
        {organizations.map((organization) => (
          <Grid
            key={organization.id}
            size={{
              xs: 12,
              md: 6,
              xl: 4,
            }}
          >
            <OrganizationCard
              organization={organization}
              onClick={() => onOrganizationClick?.(organization)}
            />
          </Grid>
        ))}
      </Grid>

      {/* =====================================================
          LOADING OVERLAY
      ===================================================== */}

      {loading && (
        <Box
          sx={{
            position: "absolute",
            inset: 0,

            zIndex: 10,

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            backgroundColor: "rgba(255, 255, 255, 0.72)",

            backdropFilter: "blur(1px)",

            pointerEvents: "none",
          }}
        >
          <CircularProgress size={28} />
        </Box>
      )}
    </Box>
  );
}
