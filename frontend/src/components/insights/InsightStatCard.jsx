import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import PhotoOutlinedIcon from "@mui/icons-material/PhotoOutlined";
import MetricAvailability from "./MetricAvailability";
import formatCompactNumber from "../../utils/formatters/formatCompactNumber";
import DashboardStatCard from "../dashboard/DashboardStatCard";

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
  const available = metric?.availability === "available";
  return (
    <DashboardStatCard
      icon={Icon}
      value={selected ? displayValue(metric) : "--"}
      label={title}
      tone={{ reach: "violet", engagement: "mint", followers: "rose", views: "sky" }[metricKey]}
      loading={loading}
      supporting={!loading && !available ? (
        <MetricAvailability
          status={selected ? metric?.availability : undefined}
          reason={metric?.reason}
          emptyText="Select an account"
          compact
        />
      ) : null}
    />
  );
}
