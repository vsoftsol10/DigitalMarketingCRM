import { Box, Card, CardContent, Skeleton, Typography } from "@mui/material";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import PhotoOutlinedIcon from "@mui/icons-material/PhotoOutlined";
import MetricAvailability from "./MetricAvailability";
import formatCompactNumber from "../../utils/formatters/formatCompactNumber";

const ICONS = {
  reach: VisibilityOutlinedIcon,
  engagement: FavoriteBorderRoundedIcon,
  followers: GroupsOutlinedIcon,
  views: PhotoOutlinedIcon,
};

function displayValue(metric) {
  if (metric?.availability !== "available" || metric.value == null) return "--";
  if (typeof metric.value === "number") return formatCompactNumber(metric.value);
  return String(metric.value);
}

export default function InsightStatCard({ title, metric, metricKey, loading, selected }) {
  const Icon = ICONS[metricKey];
  return (
    <Card elevation={0} sx={{ height: { xs: 126, sm: 132 }, border: "1px solid #E5EAF2", borderRadius: "18px", bgcolor: "#fff", boxShadow: "0 2px 7px rgba(22, 42, 78, 0.07)" }}>
      <CardContent sx={{ p: { xs: 2.25, sm: 2.75 }, height: "100%", display: "flex", flexDirection: "column", alignItems: "flex-start", "&:last-child": { pb: { xs: 2.25, sm: 2.75 } } }}>
        <Box sx={{ minHeight: 20, display: "flex", alignItems: "center", gap: 1.1 }}>
          <Icon sx={{ color: "#64748B", fontSize: 19 }} />
          <Typography sx={{ color: "#718096", fontSize: 13, fontWeight: 600, letterSpacing: 0.25, textTransform: "uppercase" }}>{title}</Typography>
        </Box>
        {loading ? (
          <Skeleton width="96px" height={39} sx={{ mt: 1 }} />
        ) : (
          <Typography sx={{ mt: 1, color: "#252B38", fontSize: 30, lineHeight: 1.12, fontWeight: 750 }}>
            {selected ? displayValue(metric) : "--"}
          </Typography>
        )}
        {!loading && metric?.availability !== "available" && (
          <Box sx={{ mt: 0.1 }}>
            <MetricAvailability
              status={selected ? metric?.availability : undefined}
              reason={metric?.reason}
              emptyText="Select an account"
              compact
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
