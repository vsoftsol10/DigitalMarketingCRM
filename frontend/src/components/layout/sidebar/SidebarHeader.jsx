import { Box, Typography } from "@mui/material";
import companyLogo from "../../reports/vsoft-logo.png?inline";

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
          bgcolor: "transparent",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <Box
          component="img"
          src={companyLogo}
          alt="The Vsoft"
          sx={{
            position: "absolute",
            width: 130,
            height: 130,
            maxWidth: "none",
            left: -40,
            top: -40,
            objectFit: "contain",
          }}
        />
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
