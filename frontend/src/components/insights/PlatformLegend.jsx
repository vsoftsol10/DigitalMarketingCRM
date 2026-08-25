import {
  Box,
  Stack,
  Typography,
} from "@mui/material";

export default function PlatformLegend({
  data = [],
}) {
  return (
    <Stack spacing={1.5}>
      {data.map((item) => (
        <Box
          key={item.platform}
          sx={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            <Box
              sx={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                bgcolor: item.color,
              }}
            />

            <Typography
              sx={{
                fontSize: 14,
                color: "#334155",
              }}
            >
              {item.platform}
            </Typography>
          </Box>

          <Typography
            sx={{
              fontSize: 14,
              fontWeight: 600,
              color: "#0F172A",
            }}
          >
            {item.value}%
          </Typography>
        </Box>
      ))}
    </Stack>
  );
}