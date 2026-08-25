import { Box, Typography } from "@mui/material";
import QueryStatsRoundedIcon from "@mui/icons-material/QueryStatsRounded";

export default function SidebarHeader() {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.8,
        px: 3,
        py: 3,
      }}
    >
      <Box
        sx={{
          width: 44,
          height: 44,
          borderRadius: "14px",
          bgcolor: "#2563EB",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
        }}
      >
        <QueryStatsRoundedIcon />
      </Box>

      <Box>
        <Typography
          sx={{
            fontSize: 16,
            fontWeight: 700,
            lineHeight: 1.2,
          }}
        >
          VSoft
        </Typography>

        <Typography
          sx={{
            fontSize: 12,
            color: "#64748B",
          }}
        >
          Marketing Agency
        </Typography>
      </Box>
    </Box>
  );
}