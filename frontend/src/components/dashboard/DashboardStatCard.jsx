import { Box, Card, CardContent, Typography } from "@mui/material";

export default function DashboardStatCard({
  icon,
  value,
  label,
}) {
  const Icon = icon;

  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "18px",
        height: 172,
      }}
    >
      <CardContent
        sx={{
          p: 2.5,

          "&:last-child": {
            pb: 2.5,
          },
        }}
      >
        {/* Icon */}

        <Box
          sx={{
            width: 42,
            height: 42,

            borderRadius: "12px",

            bgcolor: "#EEF4FF",

            display: "flex",
            justifyContent: "center",
            alignItems: "center",

            mb: 2.5,
          }}
        >
          <Icon
            sx={{
              color: "#2563EB",
              fontSize: 22,
            }}
          />
        </Box>

        {/* Value */}

        <Typography
          sx={{
            fontSize: 28,
            fontWeight: 700,
            color: "#0F172A",
            lineHeight: 1,
          }}
        >
          {value}
        </Typography>

        {/* Label */}

        <Typography
          sx={{
            mt: 1,

            fontSize: 15,

            fontWeight: 500,

            color: "#64748B",
          }}
        >
          {label}
        </Typography>
      </CardContent>
    </Card>
  );
}