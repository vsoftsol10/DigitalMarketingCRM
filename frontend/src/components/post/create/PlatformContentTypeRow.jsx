import {
  Box,
  ButtonBase,
  Grid,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import KeyboardArrowDownRoundedIcon from "@mui/icons-material/KeyboardArrowDownRounded";

import toast from "react-hot-toast";

import { useState } from "react";

import { PLATFORM_COLORS } from "../../../constants/platforms/platformColors";
import { TYPOGRAPHY } from "../../../theme/typography";

// ============================================================
// PLATFORM ICONS
// ============================================================

const PLATFORM_ICONS = {
  instagram: InstagramIcon,
  facebook: FacebookRoundedIcon,
  linkedin: LinkedInIcon,
  youtube: YouTubeIcon,
};

// ============================================================
// LABEL FORMATTER
// ============================================================

function formatLabel(value = "") {
  return value
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

// ============================================================
// COMPONENT
// ============================================================

export default function PlatformContentTypeRow({
  platform,
  contentTypes = [],
  value = "",
  onChange,
  invalidSelection = false,
  invalidReason = "",
  noAvailableType = false,
}) {
  const platformKey = platform?.icon?.toLowerCase();

  const colors = PLATFORM_COLORS[platformKey];

  const Icon = PLATFORM_ICONS[platformKey];

  const [anchorEl, setAnchorEl] = useState(null);

  const menuOpen = Boolean(anchorEl);

  const selectedOption = contentTypes.find((item) => item.value === value);

  // ============================================================
  // OPEN
  // ============================================================

  function handleOpen(event) {
    setAnchorEl(event.currentTarget);
  }

  // ============================================================
  // CLOSE
  // ============================================================

  function handleClose() {
    setAnchorEl(null);
  }

  // ============================================================
  // OPTION
  // ============================================================

  function handleOptionClick(option) {
    // ----------------------------------------------------------
    // UNSUPPORTED
    // ----------------------------------------------------------

    if (!option.available) {
      toast.error(
        option.reason ||
          "This content type is not compatible with the selected media.",
      );

      return;
    }

    // ----------------------------------------------------------
    // SUPPORTED
    // ----------------------------------------------------------

    if (typeof onChange === "function") {
      onChange(option.value);
    }

    handleClose();
  }

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Grid container spacing={2} alignItems="flex-start">
      {/* ======================================================
          PLATFORM
      ====================================================== */}

      <Grid
        size={{
          xs: 12,
          md: 4,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
            minHeight: 48,
          }}
        >
          {/* ==================================================
              PLATFORM ICON
          ================================================== */}

          <Box
            sx={{
              width: 40,
              height: 40,

              borderRadius: "11px",

              bgcolor: colors?.iconBg || "#F1F5F9",

              display: "flex",

              alignItems: "center",

              justifyContent: "center",

              flexShrink: 0,
            }}
          >
            {Icon && (
              <Icon
                sx={{
                  fontSize: 20,

                  color: colors?.iconColor || "#475569",
                }}
              />
            )}
          </Box>

          {/* ==================================================
              PLATFORM INFO
          ================================================== */}

          <Box
            sx={{
              minWidth: 0,
            }}
          >
            <Typography
              sx={{
                ...TYPOGRAPHY.inputLabel,

                fontSize: 14,

                fontWeight: 600,
              }}
            >
              {platform.name}
            </Typography>

            {/* =================================================
                NO AVAILABLE CONTENT TYPE
            ================================================= */}

            {!invalidSelection && noAvailableType && (
              <Typography
                sx={{
                  mt: 0.25,

                  fontSize: 11.5,

                  lineHeight: 1.4,

                  color: "text.secondary",
                }}
              >
                No compatible content type
              </Typography>
            )}
          </Box>
        </Box>
      </Grid>

      {/* ======================================================
          CONTENT TYPE
      ====================================================== */}

      <Grid
        size={{
          xs: 12,
          md: 8,
        }}
      >
        <ButtonBase
          type="button"
          onClick={handleOpen}
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          sx={{
            width: "100%",

            minHeight: 40,

            px: 1.5,

            display: "flex",

            alignItems: "center",

            justifyContent: "space-between",

            border: "1px solid",

            borderColor: invalidSelection ? "error.main" : "divider",

            borderRadius: 2,

            bgcolor: "background.paper",

            textAlign: "left",

            transition: "border-color .2s ease, background-color .2s ease",

            "&:hover": {
              borderColor: invalidSelection ? "error.main" : "primary.main",

              bgcolor: "action.hover",
            },

            "&:focus-visible": {
              outline: "2px solid",

              outlineColor: invalidSelection ? "error.main" : "primary.main",

              outlineOffset: 2,
            },
          }}
        >
          <Typography
            sx={{
              fontSize: 13.5,

              color: selectedOption
                ? "text.primary"
                : invalidSelection
                  ? "error.main"
                  : "text.secondary",

              fontWeight: selectedOption ? 500 : 400,
            }}
          >
            {selectedOption
              ? formatLabel(selectedOption.value)
              : "Select Content Type"}
          </Typography>

          <KeyboardArrowDownRoundedIcon
            sx={{
              fontSize: 20,

              color: invalidSelection ? "error.main" : "text.secondary",
            }}
          />
        </ButtonBase>

        {/* ====================================================
            SINGLE ERROR MESSAGE
        ==================================================== */}

        {invalidSelection && (
          <Typography
            sx={{
              mt: 0.75,

              fontSize: 12,

              lineHeight: 1.5,

              color: "error.main",

              fontWeight: 500,
            }}
          >
            {invalidReason}
          </Typography>
        )}

        {/* ====================================================
            MENU
        ==================================================== */}

        <Menu
          anchorEl={anchorEl}
          open={menuOpen}
          onClose={handleClose}
          anchorOrigin={{
            vertical: "bottom",
            horizontal: "left",
          }}
          transformOrigin={{
            vertical: "top",
            horizontal: "left",
          }}
          slotProps={{
            paper: {
              sx: {
                mt: 0.75,

                minWidth: 260,

                maxHeight: 320,

                borderRadius: 2,
              },
            },
          }}
        >
          {/* ==================================================
              EMPTY
          ================================================== */}

          {contentTypes.length === 0 && (
            <MenuItem disabled>
              <Typography
                sx={{
                  fontSize: 13,

                  color: "text.secondary",
                }}
              >
                No content types available
              </Typography>
            </MenuItem>
          )}

          {/* ==================================================
              OPTIONS
          ================================================== */}

          {contentTypes.map((option) => {
            const available = Boolean(option.available);

            return (
              <MenuItem
                key={option.value}
                selected={option.value === value}
                onClick={() => handleOptionClick(option)}
                sx={{
                  minHeight: 42,

                  px: 1.5,

                  borderRadius: 1,

                  mx: 0.5,

                  opacity: available ? 1 : 0.5,

                  cursor: available ? "pointer" : "not-allowed",

                  "&.Mui-selected": {
                    bgcolor: available ? "action.selected" : "transparent",
                  },

                  "&.Mui-selected:hover": {
                    bgcolor: available ? "action.hover" : "transparent",
                  },

                  "&:hover": available
                    ? {
                        bgcolor: "action.hover",
                      }
                    : {
                        bgcolor: "transparent",
                      },
                }}
              >
                <Box
                  sx={{
                    width: "100%",

                    display: "flex",

                    alignItems: "center",

                    justifyContent: "space-between",

                    gap: 2,
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: 13.5,

                      fontWeight: available ? 500 : 400,

                      color: available ? "text.primary" : "text.secondary",
                    }}
                  >
                    {formatLabel(option.value)}
                  </Typography>

                  {!available && (
                    <Typography
                      sx={{
                        fontSize: 11,

                        color: "text.disabled",

                        whiteSpace: "nowrap",
                      }}
                    >
                      Not available
                    </Typography>
                  )}
                </Box>
              </MenuItem>
            );
          })}
        </Menu>
      </Grid>
    </Grid>
  );
}
