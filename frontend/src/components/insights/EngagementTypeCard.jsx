import {
  Box,
  Card,
  CardContent,
  Typography,
} from "@mui/material";

import EngagementTypeChart from "./EngagementTypeChart";

export default function EngagementTypeCard({
  data = [],
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
          p: 4,

          height: "100%",

          display: "flex",
          flexDirection: "column",

          "&:last-child": {
            pb: 4,
          },
        }}
      >
        {/* Header */}

        <Typography
          sx={{
            fontSize: 18,
            fontWeight: 700,
            color: "#1E293B",
          }}
        >
          Engagement by type
        </Typography>

        <Typography
          sx={{
            mt: 0.5,
            fontSize: 15,
            color: "#64748B",
          }}
        >
          Average interactions
        </Typography>

        {/* Chart */}

        <Box
          sx={{
            flex: 1,

            mt: 2,

            display: "flex",
            alignItems: "flex-end",
          }}
        >
          <EngagementTypeChart
            data={data}
          />
        </Box>
      </CardContent>
    </Card>
  );
}