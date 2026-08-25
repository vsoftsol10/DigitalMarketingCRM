import {
  Box,
  Stack,
  Typography,
} from "@mui/material";

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

  const hasSchedule =
    publishType === "SCHEDULE" &&
    publishDate &&
    publishTime;

  let Icon = CalendarMonthRoundedIcon;
  let title = "Scheduled";
  let description =
    "Select a date and time to schedule this post.";

  if (publishType === "NOW") {
    Icon = BoltRoundedIcon;
    title = "Publish immediately";
    description =
      "This post will be published immediately.";
  }

  if (publishType === "DRAFT") {
    Icon = DraftsOutlinedIcon;
    title = "Saved as draft";
    description =
      "This post will be saved for later.";
  }

  if (hasSchedule) {
    const formattedDate =
      dayjs(publishDate).format("MMM DD, YYYY");

    const formattedTime =
      dayjs(
        `2000-01-01 ${publishTime}`
      ).format("hh:mm A");

    description = `${formattedDate} • ${formattedTime} ${timezone || ""}`;
  }

  return (
    <Box
      sx={{
        px: 1.5,
        py: 1.25,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
        bgcolor: "background.default",
      }}
    >
      <Stack
        direction="row"
        spacing={1.25}
        alignItems="center"
      >
        <Box
          sx={{
            width: 32,
            height: 32,
            flexShrink: 0,
            borderRadius: 1.5,
            bgcolor: "action.hover",
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

        <Box sx={{ minWidth: 0 }}>
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