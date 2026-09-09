// import {
//   Box,
//   Paper,
//   Stack,
//   Typography,
// } from "@mui/material";

// import ContentCopyOutlinedIcon from "@mui/icons-material/ContentCopyOutlined";
// import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";

// import toast from "react-hot-toast";

// import SecondaryButton from "../../../ui/button/SecondaryButton";
// import PrimaryButton from "../../../ui/button/PrimaryButton";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// export default function AISuggestionCard({
//   suggestion,
//   onUse,
// }) {
//   async function handleCopy() {
//     await navigator.clipboard.writeText(
//       suggestion.caption
//     );

//     toast.success("Caption copied");
//   }

//   return (
//     <Paper
//       elevation={0}
//       sx={{
//         p: 3,
//         border: "1px solid #E2E8F0",
//         borderRadius: "18px",
//       }}
//     >
//       <Typography
//         sx={{
//           ...TYPOGRAPHY.cardTitle,
//           mb: 1,
//         }}
//       >
//         {suggestion.title}
//       </Typography>

//       <Typography
//         sx={{
//           ...TYPOGRAPHY.body,
//           whiteSpace: "pre-wrap",
//         }}
//       >
//         {suggestion.caption}
//       </Typography>

//       <Stack
//         direction="row"
//         spacing={2}
//         sx={{
//           mt: 3,
//         }}
//       >
//         <PrimaryButton
//           fullWidth
//           startIcon={
//             <CheckCircleOutlineRoundedIcon />
//           }
//           onClick={() => onUse(suggestion)}
//         >
//           Use Caption
//         </PrimaryButton>

//         <SecondaryButton
//           fullWidth
//           startIcon={
//             <ContentCopyOutlinedIcon />
//           }
//           onClick={handleCopy}
//         >
//           Copy
//         </SecondaryButton>
//       </Stack>
//     </Paper>
//   );
// }

import { Box, Stack, Typography } from "@mui/material";

import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import RefreshRoundedIcon from "@mui/icons-material/RefreshRounded";
import CheckRoundedIcon from "@mui/icons-material/CheckRounded";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function AISuggestionCard({
  suggestion,
  onUse,
  onRegenerate,
}) {
  // ============================================================
  // INVALID SUGGESTION
  // ============================================================

  if (!suggestion?.caption) {
    return null;
  }

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Box
      sx={{
        width: "100%",
        boxSizing: "border-box",

        px: 1.75,
        py: 1.5,

        border: "1px solid",
        borderColor: "divider",

        borderRadius: "12px",

        bgcolor: "background.paper",

        overflow: "hidden",

        transition:
          "border-color 0.2s ease, box-shadow 0.2s ease",

        "&:hover": {
          borderColor: "rgba(37, 99, 235, 0.25)",
          boxShadow:
            "0 3px 10px rgba(15, 23, 42, 0.05)",
        },
      }}
    >
      {/* ========================================================
          HEADER
      ======================================================== */}

      <Stack
        direction="row"
        alignItems="center"
        spacing={0.75}
        sx={{
          mb: 1,
        }}
      >
        <AutoAwesomeRoundedIcon
          sx={{
            fontSize: 17,
            color: "primary.main",
            flexShrink: 0,
          }}
        />

        <Typography
          component="span"
          sx={{
            ...TYPOGRAPHY.cardTitle,

            fontSize: 13,
            fontWeight: 600,
            lineHeight: 1.4,

            color: "text.primary",

            m: 0,
          }}
        >
          AI Generated Caption
        </Typography>
      </Stack>

      {/* ========================================================
          GENERATED CAPTION
      ======================================================== */}

      <Typography
        sx={{
          ...TYPOGRAPHY.body,

          fontSize: 14,
          lineHeight: 1.65,

          color: "text.primary",

          whiteSpace: "pre-wrap",
          overflowWrap: "anywhere",
          wordBreak: "break-word",

          m: 0,
        }}
      >
        {suggestion.caption}
      </Typography>

      {/* ========================================================
          ACTIONS
      ======================================================== */}

      <Box
        sx={{
          width: "100%",

          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",

          mt: 1.25,
        }}
      >
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="flex-end"
          spacing={0.75}
          sx={{
            ml: "auto",
            width: "fit-content",
            flexShrink: 0,
          }}
        >
          {/* ==================================================
              REGENERATE
          ================================================== */}

          {typeof onRegenerate === "function" && (
            <Box
              component="button"
              type="button"
              onClick={onRegenerate}
              aria-label="Regenerate caption"
              sx={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",

                gap: 0.5,

                height: 30,
                px: 1,

                border: "1px solid",
                borderColor: "divider",

                borderRadius: "7px",

                bgcolor: "transparent",
                color: "text.secondary",

                cursor: "pointer",

                fontFamily: "inherit",
                fontSize: 12,
                fontWeight: 600,

                whiteSpace: "nowrap",

                transition:
                  "background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease",

                "&:hover": {
                  bgcolor: "action.hover",
                  borderColor: "primary.main",
                  color: "primary.main",
                },

                "&:focus-visible": {
                  outline: "2px solid",
                  outlineColor: "primary.main",
                  outlineOffset: 2,
                },

                "&:active": {
                  transform: "translateY(1px)",
                },
              }}
            >
              <RefreshRoundedIcon
                sx={{
                  fontSize: 15,
                }}
              />

              Regenerate
            </Box>
          )}

          {/* ==================================================
              USE CAPTION
          ================================================== */}

          <Box
            component="button"
            type="button"
            onClick={() => onUse?.(suggestion)}
            disabled={typeof onUse !== "function"}
            aria-label="Use generated caption"
            sx={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",

              gap: 0.5,

              height: 30,
              px: 1.25,

              border: "1px solid",
              borderColor: "primary.main",

              borderRadius: "7px",

              bgcolor: "primary.main",
              color: "primary.contrastText",

              cursor:
                typeof onUse === "function"
                  ? "pointer"
                  : "not-allowed",

              fontFamily: "inherit",
              fontSize: 12,
              fontWeight: 600,

              whiteSpace: "nowrap",

              transition:
                "background-color 0.15s ease, border-color 0.15s ease, transform 0.15s ease",

              "&:hover": {
                bgcolor: "primary.dark",
                borderColor: "primary.dark",
              },

              "&:focus-visible": {
                outline: "2px solid",
                outlineColor: "primary.main",
                outlineOffset: 2,
              },

              "&:active": {
                transform: "translateY(1px)",
              },

              "&:disabled": {
                opacity: 0.5,
                cursor: "not-allowed",
              },
            }}
          >
            <CheckRoundedIcon
              sx={{
                fontSize: 15,
              }}
            />

            Use Caption
          </Box>
        </Stack>
      </Box>
    </Box>
  );
}