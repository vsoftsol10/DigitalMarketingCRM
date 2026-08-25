import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

export default function LineChart({
  data,
  dataKey,
}) {
  return (
    <ResponsiveContainer
      width="100%"
      height="100%"
    >
      <AreaChart data={data}>
        <defs>
          <linearGradient
            id="growth"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop
              offset="5%"
              stopColor="#2563EB"
              stopOpacity={0.22}
            />

            <stop
              offset="95%"
              stopColor="#2563EB"
              stopOpacity={0}
            />
          </linearGradient>
        </defs>

        <XAxis
          dataKey="month"
          axisLine={false}
          tickLine={false}
          tick={{
            fontSize: 12,
            fill: "#94A3B8",
          }}
        />

        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{
            fontSize: 12,
            fill: "#94A3B8",
          }}
        />

        <Tooltip />

        <Area
          type="monotone"
          dataKey={dataKey}
          stroke="#2563EB"
          strokeWidth={3}
          fill="url(#growth)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}