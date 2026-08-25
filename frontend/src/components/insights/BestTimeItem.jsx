import {
  Box,
  LinearProgress,
  Typography,
} from "@mui/material";

export default function BestTimeItem({
  item,
}) {
  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          mb: 0.7,
        }}
      >
        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 600,
            color: "#334155",
          }}
        >
          {item.day}
        </Typography>

        <Typography
          sx={{
            fontSize: 14,
            color: "#64748B",
          }}
        >
          {item.hour}
        </Typography>
      </Box>

      <LinearProgress
        variant="determinate"
        value={item.score}
        sx={{
          height: 8,
          borderRadius: 999,

          bgcolor: "#E2E8F0",

          "& .MuiLinearProgress-bar": {
            borderRadius: 999,
            bgcolor: "#2563EB",
          },
        }}
      />
    </Box>
  );
}