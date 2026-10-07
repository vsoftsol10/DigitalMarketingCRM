import { Avatar, Box, Card, CardContent, Chip, Skeleton, Stack, Typography } from "@mui/material";
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import MetricAvailability from "./MetricAvailability";
import PlatformBadge from "./PlatformBadge";
import formatCompactNumber from "../../utils/formatters/formatCompactNumber";

const CHART_METRICS = [
  ["reach", "Reach"],
  ["engagement", "Engagement"],
  ["followers", "Followers"],
];

function metricPeriod(period) {
  if (period === "current") return "Current";
  if (period === "selected_range") return "Selected period";
  return "";
}

function CategoryTick({ x, y, payload }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <text textAnchor="middle" fill="#52647C" fontSize={10} fontWeight={600}>
        {payload?.value}
      </text>
    </g>
  );
}

function renderValueLabel(props) {
  const { x, y, width, value } = props;
  return (
    <text x={x + width / 2} y={y - 7} textAnchor="middle" fill="#344966" fontSize={10.5} fontWeight={700}>
      {formatCompactNumber(value)}
    </text>
  );
}

export default function AccountPerformanceCard({ account, performance, mediaCount, loading, selected }) {
  const metrics = performance?.metrics || {};
  const accountName = account?.username
    ? `@${account.username.replace(/^@/, "")}`
    : account?.display_name || account?.account_name || account?.platform_account_id || "Selected account";
  const chartData = CHART_METRICS.flatMap(([key, label]) => {
    const metric = metrics[key];
    if (!metric || metric.availability !== "available" || typeof metric.value !== "number") return [];
    return [{ label, value: metric.value, period: metricPeriod(metric.period) }];
  });
  if (typeof mediaCount === "number" && Number.isFinite(mediaCount)) {
    chartData.push({ label: "Posts", value: mediaCount, period: "Account total" });
  }
  const unavailableMetrics = CHART_METRICS
    .map(([key, label]) => ({ metric: metrics[key], label }))
    .filter(({ metric }) => metric && (metric.availability !== "available" || metric.value == null));

  return (
    <Card elevation={0} sx={{ height: { xs: "auto", lg: 354 }, minHeight: 354, border: "1px solid #E5EAF2", borderRadius: "16px", bgcolor: "#fff", boxShadow: "0 3px 12px rgba(22, 42, 78, 0.035)" }}>
      <CardContent sx={{ p: { xs: 2, sm: 2.5 }, height: "100%", display: "flex", flexDirection: "column", "&:last-child": { pb: { xs: 2, sm: 2.5 } } }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 1.2, minWidth: 0 }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ color: "#172B4D", fontSize: 17, lineHeight: 1.25, fontWeight: 700 }}>Platform &amp; Account Performance</Typography>
            <Typography sx={{ mt: 0.4, color: "#718096", fontSize: 11.5 }}>Performance for the selected account.</Typography>
          </Box>
          {selected && !loading && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.7, flexShrink: 0 }}>
              <Avatar src={account?.profile_image || undefined} sx={{ width: 30, height: 30, bgcolor: "#F2EEFF", color: "#6658EF", fontSize: 12, fontWeight: 700 }}>
                {(account?.display_name || account?.account_name || "?").slice(0, 1).toUpperCase()}
              </Avatar>
              <Box sx={{ minWidth: 0, maxWidth: { xs: 105, sm: 114 } }}>
                <Typography noWrap title={accountName} sx={{ color: "#334766", fontSize: 11, fontWeight: 650 }}>{accountName}</Typography>
                <PlatformBadge platform={account?.platform} />
              </Box>
            </Box>
          )}
        </Box>

        {loading ? (
          <Stack spacing={1.2} sx={{ mt: 2.5 }}>
            <Skeleton variant="rounded" height={220} sx={{ borderRadius: 3 }} />
          </Stack>
        ) : !selected ? (
          <Box sx={{ mt: 2, flex: 1, minHeight: 220, display: "grid", placeItems: "center", textAlign: "center", border: "1px dashed #DCE5F0", borderRadius: 3, bgcolor: "#F8FAFD" }}>
            <MetricAvailability emptyText="Select an account to view performance" />
          </Box>
        ) : (
          <Box role="group" aria-label={`Performance chart for ${accountName}`} sx={{ mt: 1.7, flex: 1, minHeight: 0, p: { xs: 1, sm: 1.35 }, display: "flex", flexDirection: "column", border: "1px solid #EEF2F7", borderRadius: 3, bgcolor: "#FCFDFE" }}>
            {chartData.length > 0 ? (
              <Box sx={{ width: "100%", minWidth: 0, flex: 1, minHeight: 185 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 23, right: 20, left: -12, bottom: 8 }} barCategoryGap="22%">
                    <CartesianGrid stroke="#E9EEF5" vertical={false} />
                    <XAxis dataKey="label" axisLine={false} tickLine={false} tick={<CategoryTick />} interval={0} height={26} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "#8A98AC" }} width={38} allowDecimals={false} />
                    <Tooltip
                      cursor={{ fill: "#F3F5FA" }}
                      formatter={(value) => [formatCompactNumber(value), "Meta value"]}
                      labelFormatter={(label, payload) => {
                        const period = payload?.[0]?.payload?.period;
                        return period ? `${label} · ${period}` : label;
                      }}
                      contentStyle={{ border: "1px solid #E5EAF2", borderRadius: 10, fontSize: 11, boxShadow: "0 8px 24px rgba(25, 42, 70, 0.1)" }}
                    />
                    <Bar dataKey="value" fill="#786DE9" radius={[5, 5, 0, 0]} barSize={28} isAnimationActive={false}>
                      <LabelList dataKey="value" content={renderValueLabel} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Box sx={{ flex: 1, minHeight: 185, display: "grid", placeItems: "center", textAlign: "center" }}>
                <Box>
                  <Typography sx={{ color: "#52647C", fontSize: 12.5, fontWeight: 650 }}>No chartable metrics returned</Typography>
                  <Typography sx={{ mt: 0.35, color: "#8290A4", fontSize: 10.5 }}>Unavailable values are not plotted as zero.</Typography>
                </Box>
              </Box>
            )}

            {unavailableMetrics.length > 0 && (
              <Box sx={{ pt: 0.7, display: "flex", alignItems: "center", gap: 0.6, flexWrap: "wrap", borderTop: "1px solid #EEF2F7" }}>
                {unavailableMetrics.map(({ metric, label }) => (
                  <Chip key={label} label={`${label}: ${metric.availability === "not_supported" ? "Not supported" : "Unavailable"}`} size="small" variant="outlined" sx={{ height: 20, borderColor: "#E5EAF2", color: "#8290A4", fontSize: 9.5 }} />
                ))}
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
