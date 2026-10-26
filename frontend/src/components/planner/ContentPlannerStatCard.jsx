import DashboardStatCard from "../dashboard/DashboardStatCard";

export default function ContentPlannerStatCard({
  icon,
  value,
  label,
  tone = "violet",
}) {
  return (
    <DashboardStatCard
      icon={icon}
      value={value}
      label={label}
      tone={tone}
    />
  );
}
