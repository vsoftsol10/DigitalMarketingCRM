import { Box, Stack } from "@mui/material";

export default function InsightsLayout({ statistics, charts, performance }) {
  return (
    <Stack spacing={1.75}>
      {statistics}
      {charts}
      <Box sx={{ minWidth: 0 }}>{performance}</Box>
    </Stack>
  );
}
