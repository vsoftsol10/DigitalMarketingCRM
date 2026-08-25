import { Box, Typography } from "@mui/material";

import ActivityIcon from "./ActivityIcon";
import formatActivityDate from "../../utils/date/formatActivityDate";
export default function ActivityItem({ activity, onClick }) {
  return (
    <Box
      onClick={() => onClick?.(activity)}
      sx={{
        display: "flex",

        alignItems: "center",

        gap: 2,

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

      <ActivityIcon type={activity.type} />

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

            lineHeight: 1.35,
          }}
        >
          {activity.title}
        </Typography>

        <Typography
          sx={{
            mt: 0.3,

            fontSize: 13,

            color: "#64748B",

            lineHeight: 1.45,
          }}
        >
          {activity.subtitle}
        </Typography>
      </Box>

      {/* Date */}

      <Typography
        sx={{
          flexShrink: 0,

          ml: 2,

          fontSize: 13,

          fontWeight: 500,

          color: "#94A3B8",
        }}
      >
        {/* {activity.created_at} */}
        {formatActivityDate(activity.created_at)}
      </Typography>
    </Box>
  );
}
