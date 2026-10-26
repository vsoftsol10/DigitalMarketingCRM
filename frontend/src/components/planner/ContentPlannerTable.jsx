// import {
//   Table,
//   TableBody,
//   TableContainer,
//   TableHead,
//   TableRow,
//   TableCell,
// } from "@mui/material";

// import ContentPlannerRow from "./ContentPlannerRow";

// export default function ContentPlannerTable({ ideas = [], onDelete }) {
//   return (
//     <TableContainer
//       sx={{
//         border: "1px solid #E2E8F0",
//         borderRadius: "18px",
//         overflow: "hidden",
//         bgcolor: "#FFFFFF",
//       }}
//     >
//       <Table
//         sx={{
//           tableLayout: "fixed",
//           width: "100%",
//         }}
//       >
//         {/* Header */}

//         <TableHead>
//           <TableRow>
//             <TableCell sx={headerStyle({ width: "28%" })}>IDEA</TableCell>

//             <TableCell sx={headerStyle()}>ORGANIZATION</TableCell>

//             <TableCell sx={headerStyle()}>PLATFORM</TableCell>

//             <TableCell sx={headerStyle()}>TYPE</TableCell>

//             <TableCell sx={headerStyle()}>GOAL</TableCell>

//             <TableCell sx={headerStyle()}>TARGET DATE </TableCell>

//             <TableCell
//               align="center"
//               sx={headerStyle({
//                 width: 70,
//               })}
//             >
//               ACTION
//             </TableCell>
//           </TableRow>
//         </TableHead>

//         {/* Body */}

//         <TableBody>
//           {ideas.map((idea) => (
//             <ContentPlannerRow key={idea.id} idea={idea} onDelete={onDelete} />
//           ))}
//         </TableBody>
//       </Table>
//     </TableContainer>
//   );
// }

// function headerStyle(extra = {}) {
//   return {
//     py: 2,

//     fontSize: 13,
//     fontWeight: 700,
//     letterSpacing: "0.05em",

//     color: "#64748B",

//     borderBottom: "1px solid #E2E8F0",

//     ...extra,
//   };
// }

import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import ContentPlannerRow from "./ContentPlannerRow";
import overviewGlassCardSx from "../organization/overview/overviewGlassCardSx";
import LoadingState from "../ui/LoadingState";

export default function ContentPlannerTable({
  ideas = [],
  onDelete,
  loading = false,
  hasActiveFilters = false,
}) {
  const hasIdeas = ideas.length > 0;

  return (
    <TableContainer
      sx={{
        ...overviewGlassCardSx,
        width: "100%",
        overflowX: "auto",
        overflowY: "hidden",
        "&::-webkit-scrollbar": { height: 8 },
        "&::-webkit-scrollbar-track": { background: "transparent" },
        "&::-webkit-scrollbar-thumb": {
          backgroundColor: "rgba(133,154,193,.42)",
          borderRadius: 10,
        },
      }}
    >
      {/* =====================================================
          TABLE-ONLY LOADING
      ===================================================== */}

      {loading && (
        <LoadingState page="Content Planner" variant="overlay" />
      )}

      <Table
        sx={{
          tableLayout: "fixed",

          width: "100%",
          minWidth: { xs: 960, md: "100%" },
          background: "transparent",
        }}
      >
        {/* ===================================================
            HEADER
        =================================================== */}

        <TableHead>
          <TableRow>
            <TableCell
              sx={headerStyle({
                width: "30%",
              })}
            >
              CAPTION
            </TableCell>

            <TableCell sx={headerStyle()}>ORGANIZATION</TableCell>

            <TableCell sx={headerStyle()}>PUBLISH ACCOUNTS</TableCell>

            <TableCell sx={headerStyle()}>TYPE</TableCell>

            <TableCell
              sx={headerStyle({
                width: 170,
              })}
            >
              TARGET DATE & TIME
            </TableCell>

            <TableCell
              align="center"
              sx={headerStyle({
                width: 80,
              })}
            >
              ACTION
            </TableCell>
          </TableRow>
        </TableHead>

        {/* ===================================================
            BODY
        =================================================== */}

        <TableBody>
          {hasIdeas ? (
            ideas.map((idea) => (
              <ContentPlannerRow
                key={idea.id}
                idea={idea}
                onDelete={onDelete}
              />
            ))
          ) : (
            <TableRow>
              <TableCell
                colSpan={6}
                sx={{
                  py: 10,

                  px: 3,

                  textAlign: "center",

                  borderBottom: "none",
                }}
              >
                <Typography
                  sx={{
                    fontSize: 14,

                    fontWeight: 600,

                    color: "#334155",
                  }}
                >
                  {hasActiveFilters
                    ? "No matching content ideas"
                    : "No content ideas found"}
                </Typography>

                <Typography
                  sx={{
                    mt: 0.75,

                    fontSize: 13,

                    lineHeight: "20px",

                    color: "#94A3B8",
                  }}
                >
                  {hasActiveFilters
                    ? "Try changing your search or filters."
                    : "Content ideas will appear here once they are created."}
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function headerStyle(extra = {}) {
  return {
    py: 2,

    px: 2,

    fontSize: 13,

    lineHeight: "18px",

    fontWeight: 700,

    letterSpacing: "0.05em",

    color: "#607493",

    backgroundColor: "rgba(224,235,251,.72)",

    borderBottom: "1px solid rgba(146,168,201,.26)",

    whiteSpace: "nowrap",

    ...extra,
  };
}
