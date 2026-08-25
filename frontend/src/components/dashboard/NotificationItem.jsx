import { Box, IconButton, Stack, Typography } from "@mui/material";

import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";

import NotificationIcon from "./NotificationIcon";

export default function NotificationItem({ notification, onClick }) {
  return (
    <Box
      sx={{
        display: "flex",

        alignItems: "flex-start",

        gap: 1.5,

        px: 2,

        py: 1.5,

        borderRadius: "16px",

        cursor: "pointer",

        transition: "0.2s",

        "&:hover": {
          bgcolor: "#F8FAFC",
        },
      }}
    >
      {/* Left Icon */}

      <NotificationIcon type={notification.type} />

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

            lineHeight: 1.3,
            color: "#1E293B",
          }}
        >
          {notification.title}
        </Typography>

        <Typography
          sx={{
            mt: 0.3,

            fontSize: 13,

            lineHeight: 1.45,

            color: "#64748B",
          }}
        >
          {notification.message}
        </Typography>

        <Typography
          sx={{
            mt: 0.6,

            fontSize: 12,

            fontWeight: 500,

            color: "#94A3B8",
          }}
        >
          {notification.organization}
        </Typography>
      </Box>

      {/* Arrow */}

      <IconButton
        size="small"
        sx={{
          mt: 0.2       ,

          color: "#94A3B8",

          flexShrink: 0,
        }}
      >
        {/* <ArrowForwardRoundedIcon /> */}
        <ArrowForwardRoundedIcon
          sx={{
            fontSize: 18,
          }}
        />
      </IconButton>
    </Box>
  );
}
