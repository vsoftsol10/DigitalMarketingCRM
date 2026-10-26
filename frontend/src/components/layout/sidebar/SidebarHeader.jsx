import { Box, Typography } from "@mui/material";
import companyLogo from "../../reports/vsoft-logo.png?inline";

export default function SidebarHeader() {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        px: 2.5,
        py: 1.5,
        "@media (max-height: 700px)": { py: 1 },
        "@media (max-height: 600px)": { py: 0.5 },
        "@media (max-height: 520px)": { py: 0 },
      }}
    >
      <Box
        sx={{
          width: 44,
          height: 44,
          borderRadius: "50%",
          bgcolor: "rgba(255,255,255,.82)",
          border: "1px solid rgba(124, 58, 237, .15)",
          boxShadow: "0 6px 16px rgba(124, 58, 237, .15)",
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
            fontSize: 17,
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
