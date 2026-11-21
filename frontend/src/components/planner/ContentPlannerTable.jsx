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
import { plannerCardSx } from "./plannerUiSx";
import PlannerLoadingState from "./PlannerLoadingState";

export default function ContentPlannerTable({
  ideas = [],
  onDelete,
  onView,
  loading = false,
  hasActiveFilters = false,
}) {
  const hasIdeas = ideas.length > 0;

  return (
    <TableContainer
      sx={{
        ...plannerCardSx,
        width: "100%",
        minHeight: loading && !hasIdeas ? 320 : undefined,
        position: "relative",
        overflowX: { xs: "hidden", md: "auto" },
        overflowY: "hidden",
        "& .MuiTable-root": {
          tableLayout: "fixed",
          width: "100%",
          minWidth: { xs: 0, md: 960 },
          background: "#FFFFFF",
        },
        "@media (max-width:899.95px)": {
          "& .MuiTableHead-root": { display: "none" },
          "& .MuiTableBody-root": {
            display: "grid",
            gap: 1.5,
            p: 1.5,
          },
          "& .MuiTableBody-root .MuiTableRow-root": {
            position: "relative",
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            border: "1px solid #E5E9F1",
            borderRadius: "16px",
            overflow: "hidden",
            background: "#FFFFFF",
            boxShadow: "0 2px 8px rgba(41,55,103,.04)",
          },
          "& .MuiTableBody-root .MuiTableCell-root": {
            display: "block",
            minWidth: 0,
            px: 1.5,
            py: 1.25,
            border: 0,
            background: "#FFFFFF",
            boxShadow: "none",
            whiteSpace: "normal",
            overflowWrap: "anywhere",
            "&::before": {
              content: "attr(data-label)",
              display: "block",
              mb: 0.5,
              color: "#94A3B8",
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: ".06em",
              lineHeight: 1.3,
            },
          },
          "& .MuiTableBody-root .MuiTableCell-root:first-of-type": {
            gridColumn: "1 / -1",
            pr: 14,
          },
          "& .MuiTableBody-root .MuiTableCell-root:nth-of-type(3)": {
            gridColumn: "1 / -1",
          },
          "& .MuiTableBody-root .MuiTableCell-root:last-of-type": {
            position: "absolute",
            top: 6,
            right: 6,
            width: "auto",
            maxWidth: "calc(100% - 12px)",
            p: 0.5,
            textAlign: "center",
            whiteSpace: "nowrap",
            "&::before": { display: "none" },
          },
          "& .MuiTableBody-root .MuiTableRow-root:hover .MuiTableCell-root": {
            background: "#FFFFFF",
          },
        },
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

      {loading && hasIdeas && (
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 320,
            zIndex: 2,
          }}
        >
          <PlannerLoadingState page="Content Planner" variant="overlay" />
        </Box>
      )}

      {loading && !hasIdeas ? (
        <PlannerLoadingState
          label="LOADING CONTENT IDEAS..."
          variant="container"
          minHeight={320}
          sx={{ height: "100%" }}
        />
      ) : (
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

            <TableCell sx={headerStyle()}>PLATFORM</TableCell>

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
                width: 142,
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
                onView={onView}
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
      )}
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

    color: "#64748B",

    backgroundColor: "#FFFFFF",

    borderBottom: "1px solid #E5E9F1",

    whiteSpace: "nowrap",

    ...extra,
  };
}
