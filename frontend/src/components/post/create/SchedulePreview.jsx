import { Box, Stack, Typography } from "@mui/material";

import CalendarMonthRoundedIcon from "@mui/icons-material/CalendarMonthRounded";
import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import DraftsOutlinedIcon from "@mui/icons-material/DraftsOutlined";

import dayjs from "dayjs";
import { useFormContext } from "react-hook-form";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function SchedulePreview() {
  const { watch } = useFormContext();

  const publishType = watch("publish_type");

  const publishDate = watch("publish_date");

  const publishTime = watch("publish_time");

  const timezone = watch("timezone");

  // ==========================================================
  // DEFAULT
  // ==========================================================

  let Icon = CalendarMonthRoundedIcon;

  let title = "Scheduled";

  let description = "Select a date and time to schedule this post.";

  // ==========================================================
  // PUBLISH NOW
  // ==========================================================

  if (publishType === "NOW") {
    Icon = BoltRoundedIcon;

    title = "Publish immediately";

    description = "This post will be published immediately.";
  }

  // ==========================================================
  // DRAFT
  // ==========================================================

  if (publishType === "DRAFT") {
    Icon = DraftsOutlinedIcon;

    title = "Saved as draft";

    description = "This post will be saved for later.";
  }

  // ==========================================================
  // SCHEDULE
  // ==========================================================

  const hasCompleteSchedule =
    publishType === "SCHEDULE" && Boolean(publishDate) && Boolean(publishTime);

  if (hasCompleteSchedule) {
    const formattedDate = dayjs(publishDate).format("MMM DD, YYYY");

    const formattedTime = dayjs(`2000-01-01 ${publishTime}`).format("hh:mm A");

    title = "Scheduled";

    description = `${formattedDate} • ${formattedTime}${
      timezone ? ` ${timezone}` : ""
    }`;
  }

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Box
      sx={{
        px: 1.5,
        py: 1.25,

        border: "1px solid",
        borderColor: "rgba(255,255,255,.9)",

        borderRadius: "14px",

        background:
          "linear-gradient(145deg, rgba(248,251,255,.86), rgba(234,242,255,.72))",
        boxShadow:
          "inset 0 1px 0 rgba(255,255,255,.95), 0 3px 8px rgba(75,96,151,.07)",
      }}
    >
      <Stack direction="row" spacing={1.25} alignItems="center">
        {/* ====================================================
            ICON
        ==================================================== */}

        <Box
          sx={{
            width: 32,
            height: 32,

            flexShrink: 0,

            borderRadius: "11px",

            background:
              "linear-gradient(145deg, rgba(255,255,255,.96), rgba(220,233,255,.86))",
            boxShadow:
              "0 3px 7px rgba(80,101,164,.12), inset 0 1px 0 rgba(255,255,255,.98)",

            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Icon
            sx={{
              fontSize: 18,
              color: "primary.main",
            }}
          />
        </Box>

        {/* ====================================================
            TEXT
        ==================================================== */}

        <Box
          sx={{
            minWidth: 0,
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.inputLabel,

              fontWeight: 600,

              lineHeight: "18px",
            }}
          >
            {title}
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,

              mt: 0.25,

              fontSize: "12px",

              lineHeight: "18px",
            }}
          >
            {description}
          </Typography>
        </Box>
      </Stack>
    </Box>
  );
}
