import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

export default function ReachChart({
  data = [],
}) {
  return (
    <ResponsiveContainer
      width="100%"
      height={300}
    >
      <AreaChart data={data}>
        <defs>
          <linearGradient
            id="reachGradient"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop
              offset="5%"
              stopColor="#2563EB"
              stopOpacity={0.25}
            />

            <stop
              offset="95%"
              stopColor="#2563EB"
              stopOpacity={0}
            />
          </linearGradient>
        </defs>

        <CartesianGrid
          stroke="#F1F5F9"
          vertical={false}
        />

        <XAxis
          dataKey="label"
          axisLine={false}
          tickLine={false}
        />

        <YAxis
          axisLine={false}
          tickLine={false}
        />

        <Tooltip />

        <Area
          type="monotone"
          dataKey="reach"
          stroke="#2563EB"
          strokeWidth={3}
          fill="url(#reachGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}