import { Box, Stack, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";

import { STATUS_ORDER, getStatusMeta } from "./statusMeta";

// The post genuinely moves through Draft → Scheduled → Published,
// in that order, so a stage track earns its place here (unlike a
// decorative numbered list). FAILED is a real branch off the
// "Scheduled" stage, so it renders as an error marker in place.

export default function CalendarEventStatusTrack({ status }) {
  const key = status?.toUpperCase();
  const failed = key === "FAILED";
  const unresolved = key === "UNRESOLVED";
  const activeIndex = failed
    ? 1
    : unresolved
      ? STATUS_ORDER.indexOf("PUBLISHING")
    : STATUS_ORDER.indexOf(key);

  return (
    <Stack
      direction="row"
      alignItems="center"
      sx={{ width: "100%" }}
    >
      {STATUS_ORDER.map((stageKey, index) => {
        const isFailedStage =
          failed && index === activeIndex;

        const meta = getStatusMeta(
          isFailedStage ? "FAILED" : stageKey
        );

        const isComplete =
          index < activeIndex ||
          (index === activeIndex && !failed);

        const isCurrent = index === activeIndex;

        const nodeColor = isFailedStage
          ? "error.main"
          : isComplete
            ? meta.palette
            : "action.disabledBackground";

        return (
          <Box
            key={stageKey}
            sx={{
              display: "flex",
              alignItems: "center",
              flex:
                index === STATUS_ORDER.length - 1
                  ? "0 0 auto"
                  : 1,
            }}
          >
            <Stack
              alignItems="center"
              spacing={0.5}
              sx={{ flexShrink: 0 }}
            >
              <Box
                sx={{
                  width: isCurrent ? 12 : 9,
                  height: isCurrent ? 12 : 9,
                  borderRadius: "50%",
                  bgcolor: nodeColor,
                  boxShadow:
                    isCurrent && stageKey !== "DRAFT"
                      ? (theme) =>
                          `0 0 0 3px ${alpha(
                            theme.palette[
                              isFailedStage
                                ? "error"
                                : "primary"
                            ].main,
                            0.16
                          )}`
                      : "none",
                  transition:
                    "all 160ms ease",
                }}
              />

              <Typography
                sx={{
                  fontSize: 11,
                  fontWeight: isCurrent ? 700 : 500,
                  color: isCurrent
                    ? isFailedStage
                      ? "error.main"
                      : "text.primary"
                    : "text.disabled",
                  whiteSpace: "nowrap",
                  letterSpacing: "0.01em",
                }}
              >
                {isFailedStage
                  ? "Failed"
                  : stageKey.charAt(0) +
                    stageKey.slice(1).toLowerCase()}
              </Typography>
            </Stack>

            {index < STATUS_ORDER.length - 1 && (
              <Box
                sx={{
                  height: 2,
                  flex: 1,
                  mx: 1,
                  mb: 2,
                  borderRadius: 1,
                  bgcolor:
                    index < activeIndex
                      ? "success.main"
                      : "divider",
                  transition:
                    "background-color 160ms ease",
                }}
              />
            )}
          </Box>
        );
      })}
    </Stack>
  );
}
