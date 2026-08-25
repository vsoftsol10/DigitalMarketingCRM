import { Chip } from "@mui/material";

import { PLATFORM_COLORS } from "../../../constants/platforms/platformColors";

export default function PlatformBadge({ platform }) {
  const colors =
    PLATFORM_COLORS[platform.icon.toLowerCase()];

  return (
    <Chip
      label={platform.name}
      size="small"
      sx={{
        height: 28,

        px: 0.5,

        borderRadius: "999px",

        bgcolor: colors.chipBg,

        color: colors.chipColor,

        fontSize: 13,

        fontWeight: 600,

        "& .MuiChip-label": {
          px: 1.2,
        },
      }}
    />
  );
}