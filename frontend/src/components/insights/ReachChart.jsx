import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import dayjs from "dayjs";

export default function ReachChart({ data = [] }) {
  const chartData = data
    .filter((point) => point.value?.availability === "available" && point.value.value != null)
    .map((point) => ({
      date: point.date,
      followers: point.value.value,
      label: dayjs(point.date).format("MMM D"),
    }));

  if (!chartData.length) return null;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 8, right: 10, left: -12, bottom: 0 }}>
        <CartesianGrid stroke="#EAF0F8" vertical={false} />
        <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#6880A5" }} minTickGap={22} />
        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#6880A5" }} width={44} />
        <Tooltip labelFormatter={(_, payload) => payload?.[0]?.payload?.date || ""} />
        <Line
          type="monotone"
          dataKey="followers"
          name="Followers"
          stroke="#6658EF"
          strokeWidth={2.75}
          activeDot={{ r: 4, fill: "#6658EF", stroke: "#fff", strokeWidth: 2 }}
          dot={{ r: 2, fill: "#6658EF", stroke: "#fff", strokeWidth: 1 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
