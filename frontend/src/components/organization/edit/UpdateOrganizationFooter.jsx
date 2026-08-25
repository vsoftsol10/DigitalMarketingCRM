// import { Box, Button, Divider } from "@mui/material";
// import SaveRoundedIcon from "@mui/icons-material/SaveRounded";
// import { useNavigate } from "react-router-dom";

// import { TYPOGRAPHY } from "../../../theme/typography";

// export default function UpdateOrganizationFooter() {
//   const navigate = useNavigate();

//   return (
//     <>
//       <Divider sx={{ my: 5 }} />

//       <Box
//         sx={{
//           display: "flex",
//           justifyContent: "flex-end",
//           alignItems: "center",
//           gap: 2,
//         }}
//       >
//         {/* Cancel */}

//         <Button
//           variant="outlined"
//           onClick={() => navigate(-1)}
//           sx={{
//             minWidth: 120,
//             height: 50,

//             borderRadius: "16px",

//             textTransform: "none",

//             borderColor: "#CBD5E1",

//             color: "#475569",

//             ...TYPOGRAPHY.formButton,

//             "&:hover": {
//               borderColor: "#94A3B8",
//               bgcolor: "#F8FAFC",
//             },
//           }}
//         >
//           Cancel
//         </Button>

//         {/* Update */}

//         <Button
//           type="submit"
//           variant="contained"
//           startIcon={<SaveRoundedIcon />}
//           sx={{
//             minWidth: 180,
//             height: 50,

//             borderRadius: "16px",

//             textTransform: "none",

//             boxShadow: "none",

//             ...TYPOGRAPHY.formButton,

//             "&:hover": {
//               boxShadow: "none",
//             },
//           }}
//         >
//           Save Changes
//         </Button>
//       </Box>
//     </>
//   );
// }

import { Box, Button, CircularProgress, Divider } from "@mui/material";

import SaveRoundedIcon from "@mui/icons-material/SaveRounded";

import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function UpdateOrganizationFooter({ loading = false }) {
  const navigate = useNavigate();

  return (
    <>
      <Divider sx={{ my: 5 }} />

      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          gap: 2,
        }}
      >
        {/* Cancel */}

        <Button
          variant="outlined"
          disabled={loading}
          onClick={() => navigate(-1)}
          sx={{
            minWidth: 120,
            height: 50,

            borderRadius: "16px",

            textTransform: "none",

            borderColor: "#CBD5E1",

            color: "#475569",

            ...TYPOGRAPHY.formButton,

            "&:hover": {
              borderColor: "#94A3B8",
              bgcolor: "#F8FAFC",
            },
          }}
        >
          Cancel
        </Button>

        {/* Update */}

        <Button
          type="submit"
          variant="contained"
          disabled={loading}
          startIcon={
            loading ? (
              <CircularProgress size={18} color="inherit" />
            ) : (
              <SaveRoundedIcon />
            )
          }
          sx={{
            minWidth: 180,
            height: 50,

            borderRadius: "16px",

            textTransform: "none",

            boxShadow: "none",

            ...TYPOGRAPHY.formButton,

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          {loading ? "Saving..." : "Save Changes"}
        </Button>
      </Box>
    </>
  );
}
