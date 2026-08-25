// import { Box } from "@mui/material";

// import SearchField from "./SearchField";
// import OrganizationFilter from "./OrganizationFilter";

// export default function ContentPlannerFilters({
//   organizations = [],
//   filters,
//   onSearchChange,
//   onOrganizationChange,
// }) {
//   return (
//     <Box
//       sx={{
//         display: "flex",
//         alignItems: "center",
//         gap: 2,

//         mt: 4,
//         mb: 4,

//         flexWrap: "wrap",
//       }}
//     >
//       {/* Search */}

//       <Box
//         sx={{
//           flex: 1,
//           minWidth: 320,
//         }}
//       >
//         <SearchField value={filters.search} onChange={onSearchChange} />
//       </Box>

//       {/* Organization Filter */}

//       <OrganizationFilter
//         value={filters.organization}
//         options={organizations}
//         onChange={onOrganizationChange}
//       />
//     </Box>
//   );
// }

import { Box, Button } from "@mui/material";

import SearchField from "./SearchField";
import OrganizationFilter from "./OrganizationFilter";

export default function ContentPlannerFilters({
  organizations = [],
  filters,
  onSearchChange,
  onOrganizationChange,
  onClearFilters,
  hasActiveFilters = false,
}) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",

        gap: 2,

        mt: 4,
        mb: 4,

        flexWrap: "wrap",
      }}
    >
      {/* =====================================================
          SEARCH
      ===================================================== */}

      <Box
        sx={{
          flex: 1,
          minWidth: 320,
        }}
      >
        <SearchField
          value={filters.search}
          onChange={onSearchChange}
          placeholder="Search content ideas..."
        />
      </Box>

      {/* =====================================================
          ORGANIZATION FILTER
      ===================================================== */}

      <OrganizationFilter
        value={filters.organization}
        options={organizations}
        onChange={onOrganizationChange}
      />

      {/* =====================================================
          CLEAR FILTERS
      ===================================================== */}

      {hasActiveFilters && (
        <Button
          type="button"
          variant="text"
          onClick={onClearFilters}
          sx={{
            height: 48,

            px: 2,

            borderRadius: "12px",

            textTransform: "none",

            fontSize: 14,
            fontWeight: 600,

            color: "#475569",

            whiteSpace: "nowrap",

            "&:hover": {
              backgroundColor: "#F8FAFC",
            },
          }}
        >
          Clear Filters
        </Button>
      )}
    </Box>
  );
}
