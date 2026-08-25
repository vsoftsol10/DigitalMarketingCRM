import {
  Card,
  CardContent,
  Typography,
} from "@mui/material";

import BestTimeList from "./BestTimeList";

export default function BestTimeCard({
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
          Best Time to Post
        </Typography>

        <Typography
          sx={{
            mt: 0.5,
            mb: 3,

            fontSize: 15,
            color: "#64748B",
          }}
        >
          Highest engagement windows
        </Typography>

        <BestTimeList
          data={data}
        />
      </CardContent>
    </Card>
  );
}