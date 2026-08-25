import {
  Card,
  CardContent,
  Typography,
} from "@mui/material";

import ReachChart from "./ReachChart";

export default function ReachChartCard({
  data,
}) {
  return (
    <Card
      elevation={0}
      sx={{
        height: 420,

        border: "1px solid #E2E8F0",

        borderRadius: "22px",
      }}
    >
      <CardContent
        sx={{
          p: 3,

          "&:last-child": {
            pb: 3,
          },
        }}
      >
        <Typography
          sx={{
            fontSize: 18,
            fontWeight: 700,
            color: "#1E293B",
          }}
        >
          Reach over time
        </Typography>

        <Typography
          sx={{
            mt: 0.5,
            mb: 3,

            fontSize: 15,

            color: "#64748B",
          }}
        >
          Last 30 days
        </Typography>

        <ReachChart
          data={data}
        />
      </CardContent>
    </Card>
  );
}