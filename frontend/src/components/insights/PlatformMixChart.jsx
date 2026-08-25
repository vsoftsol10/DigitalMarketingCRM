import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function PlatformMixChart({
  data = [],
}) {
  return (
    <ResponsiveContainer
      width="100%"
      height={220}
    >
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          innerRadius={58}
          outerRadius={82}
          paddingAngle={3}
        >
          {data.map((item) => (
            <Cell
              key={item.platform}
              fill={item.color}
            />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}