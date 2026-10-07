import { Box, Card, CardContent, Skeleton, Typography } from "@mui/material";
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import ArrowUpwardRoundedIcon from "@mui/icons-material/ArrowUpwardRounded";
import ArrowDownwardRoundedIcon from "@mui/icons-material/ArrowDownwardRounded";
import ReachChart from "./ReachChart";
import MetricAvailability from "./MetricAvailability";
import formatCompactNumber from "../../utils/formatters/formatCompactNumber";

export default function ReachChartCard({ growth, durationLabel, loading, selected }) {
  const points = growth?.points || [];
  const current = growth?.current_value;
  const change = growth?.change;
  const hasChart = points.some((point) => point.value?.availability === "available" && point.value.value != null);
  const changeAvailable = change?.availability === "available" && typeof change.value === "number";
  const positive = changeAvailable && change.value >= 0;

  return (
    <Card elevation={0} sx={{ height: { xs: "auto", lg: 354 }, minHeight: 354, border: "1px solid #E5EAF2", borderRadius: "16px", bgcolor: "#fff", boxShadow: "0 3px 12px rgba(22, 42, 78, 0.035)" }}>
      <CardContent sx={{ p: { xs: 2, sm: 2.5 }, height: "100%", display: "flex", flexDirection: "column", "&:last-child": { pb: { xs: 2, sm: 2.5 } } }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, mb: 1.7 }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ color: "#172B4D", fontSize: 18, fontWeight: 700 }}>Overall Follower Growth</Typography>
            <Typography sx={{ mt: 0.4, color: "#718096", fontSize: 12.5 }}>
              Track how the selected account&apos;s followers changed over time.
            </Typography>
          </Box>
          {selected && !loading && current?.availability === "available" && current.value != null && (
            <Box sx={{ flexShrink: 0, textAlign: "right" }}>
              <Typography sx={{ color: "#172B4D", fontSize: 23, lineHeight: 1.2, fontWeight: 700 }}>
                {formatCompactNumber(current.value)}
              </Typography>
              <Typography sx={{ color: "#7185A5", fontSize: 11.5 }}>Total Followers</Typography>
              <Box sx={{ mt: 0.35, display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 0.3 }}>
                {changeAvailable && (positive
                  ? <ArrowUpwardRoundedIcon sx={{ fontSize: 14, color: "#04A77B" }} />
                  : <ArrowDownwardRoundedIcon sx={{ fontSize: 14, color: "#E0445E" }} />)}
                <Typography sx={{ color: changeAvailable ? (positive ? "#04A77B" : "#E0445E") : "#7185A5", fontSize: 11.5 }}>
                  {changeAvailable ? `${formatCompactNumber(change.value)} vs previous period` : "Change unavailable"}
                </Typography>
              </Box>
            </Box>
          )}
        </Box>
        {loading ? (
          <Skeleton variant="rounded" height={225} sx={{ borderRadius: 3 }} />
        ) : hasChart ? (
          <Box sx={{ height: 225, width: "100%", minWidth: 0 }}><ReachChart data={points} /></Box>
        ) : (
          <Box sx={{ height: 225, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", borderRadius: 3, bgcolor: "#F8FAFD", border: "1px dashed #DCE5F0" }}>
            <Box sx={{ maxWidth: 340, px: 2 }}>
              <Box sx={{ width: 42, height: 42, mx: "auto", mb: 1.2, display: "grid", placeItems: "center", borderRadius: "50%", bgcolor: "#EEF2FF", color: "#6674D9" }}>
                <TrendingUpRoundedIcon sx={{ fontSize: 21 }} />
              </Box>
              <Typography sx={{ color: "#334766", fontSize: 14, fontWeight: 650 }}>
                {selected ? "Follower growth data unavailable" : "Select an account to view follower growth"}
              </Typography>
              {selected && (
                growth?.reason === "metric_value_not_returned" ? (
                  <Typography sx={{ mt: 0.45, color: "#718096", fontSize: 12.5 }}>
                    Instagram did not return follower history for the selected period.
                  </Typography>
                ) : (
                  <Box sx={{ mt: 0.5 }}>
                    <MetricAvailability status={growth?.availability} reason={growth?.reason || current?.reason} />
                  </Box>
                )
              )}
            </Box>
          </Box>
        )}
        <Typography sx={{ mt: "auto", pt: 0.8, color: "#8597B3", fontSize: 11, textAlign: "right" }}>{durationLabel}</Typography>
      </CardContent>
    </Card>
  );
}
