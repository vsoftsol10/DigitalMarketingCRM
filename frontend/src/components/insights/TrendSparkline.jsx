import {
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";

export default function TrendSparkline({
  data = [],
}) {
  const chartData = data.map((value, index) => ({
    id: index,
    value,
  }));

  return (
    <ResponsiveContainer
      width={90}
      height={40}
    >
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke="#22C55E"
          strokeWidth={2.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}