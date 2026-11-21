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
          minWidth: { xs: "100%", md: 280 },
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
            minHeight: 44,
            width: { xs: "100%", sm: "auto" },

            px: 2,

            borderRadius: "12px",

            textTransform: "none",

            fontSize: 14,
            fontWeight: 600,

            color: "#475569",

            whiteSpace: "nowrap",

          border: "1px solid #D8DEEA",
          background: "#FFFFFF",
          boxShadow: "none",

            "&:hover": {
              background: "#F5F2FF",
              borderColor: "#CFC5F8",
              color: "#6941D9",
            },

            "&:focus-visible": {
              outline: "2px solid rgba(111,145,211,.48)",
              outlineOffset: 2,
            },
          }}
        >
          Clear Filters
        </Button>
      )}
    </Box>
  );
}
