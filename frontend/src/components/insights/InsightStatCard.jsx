import { Box, Card, CardContent, Typography } from "@mui/material";

export default function InsightStatCard({
  title,
  value,
  change,
  positive = true,
}) {
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "18px",
        height: 150,
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
        {/* Title */}

        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 600,
            color: "#64748B",
          }}
        >
          {title}
        </Typography>

        {/* Value */}

        <Typography
          sx={{
            mt: 2,

            fontSize: 34,
            fontWeight: 700,
            color: "#0F172A",
            lineHeight: 1,
          }}
        >
          {value}
        </Typography>

        {/* Change */}

        <Typography
          sx={{
            mt: 2,

            fontSize: 14,
            fontWeight: 600,

            color: positive
              ? "#16A34A"
              : "#DC2626",
          }}
        >
          {positive ? "+" : ""}
          {change}%
        </Typography>
      </CardContent>
    </Card>
  );
}