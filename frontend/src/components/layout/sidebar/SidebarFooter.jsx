import { Avatar, Box, Typography } from "@mui/material";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { useNavigate } from "react-router-dom";

export default function SidebarFooter() {
  const navigate = useNavigate();

  return (
    <Box
      onClick={() => navigate("/settings")}
      sx={{
        px: 2.5,
        py: 2,
        display: "flex",
        alignItems: "center",
        cursor: "pointer",
        transition: "all .2s ease",

        "&:hover": {
          bgcolor: "#F8FAFC",
        },
      }}
    >
      <Avatar
        sx={{
          width: 42,
          height: 42,
          bgcolor: "#2563EB",
          fontSize: 14,
          fontWeight: 600,
          mr: 1.8,
        }}
      >
        MK
      </Avatar>

      <Box
        sx={{
          flex: 1,
          overflow: "hidden",
        }}
      >
        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 600,
            color: "#0F172A",
            lineHeight: 1.2,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          Muthukrishnan
        </Typography>

        <Typography
          sx={{
            fontSize: 12,
            color: "#64748B",
            mt: 0.3,
            lineHeight: 1.2,
          }}
        >
          Agency Admin
        </Typography>
      </Box>

      <ChevronRightIcon
        sx={{
          fontSize: 20,
          color: "#94A3B8",
        }}
      />
    </Box>
  );
}