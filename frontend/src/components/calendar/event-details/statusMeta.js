import EditNoteRoundedIcon from "@mui/icons-material/EditNoteRounded";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import SyncRoundedIcon from "@mui/icons-material/SyncRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import ErrorRoundedIcon from "@mui/icons-material/ErrorRounded";

// Single source of truth for status → label / color / icon.
// Keeping this in one place is what keeps the header chip, the
// status track, and the footer actions visually in sync.

export const STATUS_ORDER = [
  "DRAFT",
  "SCHEDULED",
  "PUBLISHING",
  "PUBLISHED",
];

export const STATUS_META = {
  DRAFT: {
    label: "Draft",
    color: "default",
    palette: "text.secondary",
    dot: "text.disabled",
    icon: EditNoteRoundedIcon,
  },
  SCHEDULED: {
    label: "Scheduled",
    color: "primary",
    palette: "primary.main",
    dot: "primary.main",
    icon: ScheduleRoundedIcon,
  },
  PUBLISHING: {
    label: "Publishing",
    color: "warning",
    palette: "warning.main",
    dot: "warning.main",
    icon: SyncRoundedIcon,
  },
  UNRESOLVED: {
    label: "Unresolved",
    color: "warning",
    palette: "warning.main",
    dot: "warning.main",
    icon: SyncRoundedIcon,
  },
  PUBLISHED: {
    label: "Published",
    color: "success",
    palette: "success.main",
    dot: "success.main",
    icon: CheckCircleRoundedIcon,
  },
  FAILED: {
    label: "Failed to publish",
    color: "error",
    palette: "error.main",
    dot: "error.main",
    icon: ErrorRoundedIcon,
  },
};

export function getStatusMeta(status) {
  const key = status?.toUpperCase();
  return (
    STATUS_META[key] || {
      label: status || "Unknown",
      color: "default",
      palette: "text.secondary",
      dot: "text.disabled",
      icon: EditNoteRoundedIcon,
    }
  );
}
