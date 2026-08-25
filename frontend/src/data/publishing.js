import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import CalendarMonthRoundedIcon from "@mui/icons-material/CalendarMonthRounded";
import DraftsOutlinedIcon from "@mui/icons-material/DraftsOutlined";

export const PUBLISH_TYPE_OPTIONS = [
  {
    value: "NOW",
    label: "Publish Now",
    description: "Publish this post immediately.",
    icon: BoltRoundedIcon,
  },
  {
    value: "SCHEDULE",
    label: "Schedule",
    description: "Choose a date and time to publish.",
    icon: CalendarMonthRoundedIcon,
  },
  {
    value: "DRAFT",
    label: "Save as Draft",
    description: "Save this post and publish it later.",
    icon: DraftsOutlinedIcon,
  },
];

export const TIMEZONE_OPTIONS = [
  {
    value: "Asia/Kolkata",
    label: "Asia / Kolkata (IST)",
  },
];