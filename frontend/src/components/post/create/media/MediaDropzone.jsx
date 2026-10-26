
import { Box, Stack, Typography } from "@mui/material";

import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import VideocamOutlinedIcon from "@mui/icons-material/VideocamOutlined";
import LayersOutlinedIcon from "@mui/icons-material/LayersOutlined";

import { useTheme } from "@mui/material/styles";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function MediaDropzone({
  config,
  onBrowse,
  onDrop,
  onDragOver,
}) {
  const theme = useTheme();

  const actionButtonSx = {
    margin: 0, // native <button> default margin fix
    height: 40,
    px: 1.5,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 0.7,
    border: "1px solid rgba(255,255,255,.96)",
    borderRadius: "13px",
    bgcolor: "rgba(242,247,255,.86)",
    color: "#526887",
    boxShadow:
      "0 4px 9px rgba(75,96,151,.1), inset 0 1px 0 rgba(255,255,255,.98), inset 0 -1px 3px rgba(112,127,177,.08)",
    cursor: "pointer",
    fontFamily: "inherit",
    fontSize: 13,
    fontWeight: 500,
    whiteSpace: "nowrap",
    transition:
      "border-color .2s ease, background-color .2s ease, color .2s ease",
    "&:hover": {
      borderColor: theme.palette.primary.main,
      bgcolor: "rgba(230,239,255,.92)",
      color: theme.palette.primary.main,
    },
    "&:focus-visible": {
      outline: "2px solid",
      outlineColor: theme.palette.primary.main,
      outlineOffset: 2,
    },
  };

  return (
    <Box
      onDrop={onDrop}
      onDragOver={onDragOver}
      sx={{
        width: "100%",
        boxSizing: "border-box",

        height: {
          xs: 265,
          sm: 280,
        },

        px: 2.5,
        py: 3,

        border: "2px dashed",
        borderColor: "#AAB9D4",

        borderRadius: "18px",

        background:
          "linear-gradient(145deg, rgba(248,251,255,.84), rgba(234,242,255,.72))",
        boxShadow:
          "inset 0 2px 5px rgba(101,122,169,.06), inset 0 1px 0 rgba(255,255,255,.9)",

        display: "flex",
        alignItems: "center",
        justifyContent: "center",

        textAlign: "center",

        transition: "border-color 0.2s ease, background-color 0.2s ease",

        "&:hover": {
          borderColor: theme.palette.primary.main,
          bgcolor: "rgba(232,241,255,.82)",
        },
      }}
    >
      <Stack
        alignItems="center"
        justifyContent="center"
        spacing={0}
        sx={{
          width: "100%",
          maxWidth: 650,
          mx: "auto",
        }}
      >
        {/* =====================================================
            UPLOAD ICON
        ===================================================== */}

        <Box
          sx={{
            width: 56,
            height: 56,

            flexShrink: 0,

            borderRadius: "50%",
            border: "1px solid rgba(255,255,255,.96)",
            background:
              "linear-gradient(145deg, rgba(255,255,255,.98), rgba(222,233,255,.9))",
            boxShadow:
              "0 6px 12px rgba(80,101,164,.14), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -2px 4px rgba(104,124,175,.1)",

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            mx: "auto",
            mb: 1.5,
          }}
        >
          <CloudUploadOutlinedIcon
            sx={{
              fontSize: 29,
              color: "#557FE1",
            }}
          />
        </Box>

        {/* =====================================================
            TITLE
        ===================================================== */}

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionTitle,

            fontSize: 16,
            fontWeight: 600,

            lineHeight: 1.4,

            color: "#4B566A",

            textAlign: "center",
            width: "100%",

            mb: 0.6,
          }}
        >
          Drag &amp; drop files here
        </Typography>

        {/* =====================================================
            DESCRIPTION
        ===================================================== */}

        <Typography
          sx={{
            ...TYPOGRAPHY.bodySmall,

            fontSize: 13,

            lineHeight: 1.5,

            color: "#8795AE",

            textAlign: "center",
            width: "100%",

            mb: 1.75,
          }}
        >
          or click to browse — images, videos, or multiple files for a carousel
        </Typography>

        {/* =====================================================
            ACTION BUTTONS
        ===================================================== */}

        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            gap: 1,
          }}
        >
          {/* ==================================================
              IMAGE
          ================================================== */}

          <Box
            component="button"
            type="button"
            // onClick={onBrowse}
            onClick={() => onBrowse?.("IMAGE")}
            sx={actionButtonSx}
          >
            <ImageOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
            Image
          </Box>

          {/* ==================================================
              VIDEO
          ================================================== */}

          <Box
            component="button"
            type="button"
            onClick={() => onBrowse?.("VIDEO")}
            // onClick={onBrowse}
            sx={actionButtonSx}
          >
            <VideocamOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
            Video
          </Box>

          {/* ==================================================
              CAROUSEL
          ================================================== */}

          <Box
            component="button"
            type="button"
            onClick={() => onBrowse?.("CAROUSEL")}
            // onClick={onBrowse}
            sx={actionButtonSx}
          >
            <LayersOutlinedIcon
              sx={{
                fontSize: 17,
              }}
            />
            Carousel
          </Box>
        </Box>
      </Stack>
    </Box>
  );
}
