import { Box, CircularProgress } from "@mui/material";

export default function TableLoadingOverlay() {
  return (
    <Box
      sx={{
        position: "absolute",
        inset: 0,

        display: "flex",
        alignItems: "center",
        justifyContent: "center",

        backgroundColor: "rgba(255, 255, 255, 0.72)",

        backdropFilter: "blur(1px)",

        zIndex: 2,
      }}
    >
      <CircularProgress size={28} />
    </Box>
  );
}
