import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";

export default function EngagementTypeChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        margin={{
          top: 45,
          right: 10,
          left: -20,
          bottom: 0,
        }}
      >
        <XAxis
          dataKey="label"
          dy={12}
          tickLine={false}
          axisLine={false}
          tick={{
            fontSize: 14,
            fill: "#64748B",
          }}
        />

        <YAxis hide />

        <Tooltip
          cursor={{
            fill: "transparent",
          }}
        />

        <Bar dataKey="value" radius={[8, 8, 0, 0]} barSize={72}>
          {data.map((item) => (
            <Cell key={item.label} fill={item.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
