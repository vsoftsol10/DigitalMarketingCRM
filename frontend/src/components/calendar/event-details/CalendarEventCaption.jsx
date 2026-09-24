import { Box, Stack, Typography } from "@mui/material";

import DescriptionRoundedIcon from "@mui/icons-material/DescriptionRounded";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function CalendarEventCaption({
  event,
}) {
  if (!event?.caption) {
    return null;
  }

  const charCount = event.caption.length;

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        mt: 2.5,
        pt: 2.5,
        borderTop: "1px solid",
        borderColor: "divider",
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ mb: 1.5 }}
      >
        <Stack
          direction="row"
          alignItems="center"
          spacing={1}
        >
          <DescriptionRoundedIcon
            sx={{
              fontSize: 18,
              color: "text.secondary",
            }}
          />

          <Typography
            component="h3"
            sx={{
              ...TYPOGRAPHY.cardTitle,
              color: "text.primary",
            }}
          >
            Caption
          </Typography>
        </Stack>

        <Typography
          sx={{
            ...TYPOGRAPHY.caption,
            color: "text.disabled",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {charCount.toLocaleString()} chars
        </Typography>
      </Stack>

      <Box
        sx={{
          position: "relative",
          width: "100%",
          minWidth: 0,
          pl: 2,
          pr: 1.5,
          py: 1.5,
          borderRadius: 2,
          bgcolor: "action.hover",
          borderLeft: "3px solid",
          borderLeftColor: "divider",
          boxSizing: "border-box",
        }}
      >
        <Typography
          sx={{
            ...TYPOGRAPHY.body,
            color: "text.primary",
            minWidth: 0,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            overflowWrap: "anywhere",
          }}
        >
          {event.caption}
        </Typography>
      </Box>
    </Box>
  );
}
