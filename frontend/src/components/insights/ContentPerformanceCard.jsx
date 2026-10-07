import { Box, Card, CardContent, Typography } from "@mui/material";
import dayjs from "dayjs";
import ContentPerformanceTable from "./ContentPerformanceTable";

export default function ContentPerformanceCard(props) {
  const since = props.content?.since;
  const until = props.content?.until;
  const start = since ? dayjs(since) : null;
  const end = until ? dayjs(until) : null;
  const snapshotRange = start?.isValid() && end?.isValid()
    ? `${start.format("MMM D, YYYY")} – ${end.format("MMM D, YYYY")}`
    : "";

  return (
    <Card elevation={0} sx={{ border: "1px solid #E5EAF2", borderRadius: "18px", bgcolor: "#fff", boxShadow: "0 3px 12px rgba(22, 42, 78, 0.035)" }}>
      <CardContent sx={{ p: { xs: 2, sm: 3 }, "&:last-child": { pb: { xs: 2, sm: 3 } } }}>
        <Box sx={{ pb: 2.1 }}>
          <Typography sx={{ color: "#252B38", fontSize: 20, lineHeight: 1.3, fontWeight: 700 }}>Content Performance</Typography>
          <Typography sx={{ mt: 0.5, color: "#718096", fontSize: 14 }}>
            Individual post-level performance{snapshotRange ? ` from ${snapshotRange}` : " from the saved snapshot"}.
          </Typography>
        </Box>
        <ContentPerformanceTable {...props} />
      </CardContent>
    </Card>
  );
}
