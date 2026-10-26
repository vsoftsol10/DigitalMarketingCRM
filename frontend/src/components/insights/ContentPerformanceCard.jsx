import { Box, Card, CardContent, Typography } from "@mui/material";
import dayjs from "dayjs";
import ContentPerformanceTable from "./ContentPerformanceTable";
import { insightsGlassSurfaceSx } from "./insightsGlassSx";

export default function ContentPerformanceCard(props) {
  const since = props.content?.since;
  const until = props.content?.until;
  const start = since ? dayjs(since) : null;
  const end = until ? dayjs(until) : null;
  const snapshotRange = start?.isValid() && end?.isValid()
    ? `${start.format("MMM D, YYYY")} – ${end.format("MMM D, YYYY")}`
    : "";

  return (
    <Card elevation={0} sx={{ width: "100%", minWidth: 0, ...insightsGlassSurfaceSx, borderRadius: "22px" }}>
      <CardContent sx={{ p: { xs: 2, sm: 3 }, "&:last-child": { pb: { xs: 2, sm: 3 } } }}>
        <Box sx={{ pb: 2.1 }}>
          <Typography sx={{ color: "#1D3157", fontSize: 20, lineHeight: 1.3, fontWeight: 750 }}>Content Performance</Typography>
          <Typography sx={{ mt: 0.5, color: "#687E9F", fontSize: 14 }}>
            Individual post-level performance{snapshotRange ? ` from ${snapshotRange}` : " from the saved snapshot"}.
          </Typography>
        </Box>
        <ContentPerformanceTable {...props} />
      </CardContent>
    </Card>
  );
}
