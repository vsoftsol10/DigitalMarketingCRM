
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
    border: "1px solid #D4DCE8",
    borderRadius: "11px",
    bgcolor: "#FFFFFF",
    color: "#4D586B",
    cursor: "pointer",
    fontFamily: "inherit",
    fontSize: 13,
    fontWeight: 500,
    whiteSpace: "nowrap",
    transition:
      "border-color .2s ease, background-color .2s ease, color .2s ease",
    "&:hover": {
      borderColor: theme.palette.primary.main,
      bgcolor: "#F8FBFF",
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

        bgcolor: "#FFFFFF",

        display: "flex",
        alignItems: "center",
        justifyContent: "center",

        textAlign: "center",

        transition: "border-color 0.2s ease, background-color 0.2s ease",

        "&:hover": {
          borderColor: theme.palette.primary.main,
          bgcolor: "#FBFDFF",
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

            borderRadius: "16px",

            bgcolor: "#EEF1F6",

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
              color: "#8B9AB5",
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
