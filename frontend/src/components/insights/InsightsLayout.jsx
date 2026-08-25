import { Box } from "@mui/material";

export default function InsightsLayout({
  statistics,
  charts,
  performance,
}) {
  return (
    <>
      {statistics}

      <Box sx={{ mt: 4 }}>
        {charts}
      </Box>

      <Box sx={{ mt: 4 }}>
        {performance}
      </Box>
    </>
  );
}