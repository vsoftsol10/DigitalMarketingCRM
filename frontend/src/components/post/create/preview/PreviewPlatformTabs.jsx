import { Box, useTheme } from "@mui/material";
import { useEffect } from "react";

import PreviewPlatformChip from "./PreviewPlatformChip";

export default function PreviewPlatformTabs({
  platforms = [],
  value,
  onChange,
}) {
  const theme = useTheme();

  useEffect(() => {
    if (!value && platforms.length) {
      onChange(platforms[0]);
    }
  }, [platforms, value, onChange]);

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1,
        px: 3,
        py: 2,
        overflowX: "auto",
        borderBottom: `1px solid ${theme.palette.divider}`,

        "&::-webkit-scrollbar": {
          display: "none",
        },
      }}
    >
      {platforms.map((platform) => (
        <PreviewPlatformChip
          key={platform}
          platform={platform}
          selected={platform === value}
          onClick={() => onChange(platform)}
        />
      ))}
    </Box>
  );
}