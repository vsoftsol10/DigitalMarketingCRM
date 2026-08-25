import {
  Card,
  CardContent,
  Typography,
} from "@mui/material";

import PlatformMixChart from "./PlatformMixChart";
import PlatformLegend from "./PlatformLegend";

export default function PlatformMixCard({
  data,
}) {
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "22px",
        height: 420,
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
          Platform Mix
        </Typography>

        <Typography
          sx={{
            mt: .5,
            mb: 2,

            fontSize: 15,

            color: "#64748B",
          }}
        >
          Reach by platform
        </Typography>

        <PlatformMixChart
          data={data}
        />

        <PlatformLegend
          data={data}
        />
      </CardContent>
    </Card>
  );
}