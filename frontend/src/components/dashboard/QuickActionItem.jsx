import {
  Box,
  IconButton,
  Typography,
} from "@mui/material";

import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";

import QuickActionIcon from "./QuickActionIcon";

export default function QuickActionItem({
  action,
  onClick,
}) {
  return (
    <Box
      onClick={() => onClick?.(action)}
      sx={{
        display: "flex",
        alignItems: "center",

        gap: 2,

        p: 2,

        border: "1px solid #E2E8F0",

        borderRadius: "16px",

        cursor: "pointer",

        transition: ".2s",

        "&:hover": {
          bgcolor: "#F8FAFC",
          borderColor: "#CBD5E1",
        },
      }}
    >
      {/* Left Icon */}

      <QuickActionIcon icon={action.icon} />

      {/* Content */}

      <Box
        sx={{
          flex: 1,
          minWidth: 0,
        }}
      >
        <Typography
          sx={{
            fontSize: 15,
            fontWeight: 600,
            color: "#1E293B",
            lineHeight: 1.4,
          }}
        >
          {action.title}
        </Typography>

        {action.description && (
          <Typography
            sx={{
              mt: 0.3,

              fontSize: 13,

              color: "#64748B",

              lineHeight: 1.45,
            }}
          >
            {action.description}
          </Typography>
        )}
      </Box>

      {/* Arrow */}

      <IconButton
        size="small"
        sx={{
          color: "#94A3B8",

          flexShrink: 0,
        }}
      >
        <ArrowForwardRoundedIcon fontSize="small" />
      </IconButton>
    </Box>
  );
}