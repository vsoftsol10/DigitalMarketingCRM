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

import { Box, Grid } from "@mui/material";

import OrganizationCard from "./OrganizationCard";
import LoadingState from "../../ui/LoadingState";

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
              xl: 6,
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
        <LoadingState page="Organizations" variant="overlay" />
      )}
    </Box>
  );
}
