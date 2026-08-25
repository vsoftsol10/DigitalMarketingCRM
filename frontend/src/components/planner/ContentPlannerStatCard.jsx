import { Card, CardContent, Typography, Box } from "@mui/material";

export default function ContentPlannerStatCard({ icon: Icon, value, label }) {
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "18px",
        height: 170,
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
        <Box
          sx={{
            width: 44,
            height: 44,

            borderRadius: "12px",

            bgcolor: "#EEF4FF",

            display: "flex",
            justifyContent: "center",
            alignItems: "center",

            mb: 3,
          }}
        >
          <Icon
            sx={{
              color: "#2563EB",
              fontSize: 22,
            }}
          />
        </Box>

        <Typography
          sx={{
            fontSize: 30,
            fontWeight: 700,
            color: "#1E293B",
          }}
        >
          {value}
        </Typography>

        <Typography
          sx={{
            mt: 0.5,

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
