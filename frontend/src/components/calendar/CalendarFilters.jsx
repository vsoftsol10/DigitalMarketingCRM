import {
  Box,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

import { TYPOGRAPHY } from "../../theme/typography";

import CalendarFilterField from "./CalendarFilterField";
import { calendarGlassSurfaceSx } from "./calendarGlassSx";

export default function CalendarFilters({
  open,
  onClose,
  filters,
  onFilterChange,
  onApply,
  onClear,
  organizations = [],
  socialAccounts = [],
  contentTypes = [],
  statuses = [],
}) {
  function handleCancel() {
    onClose?.();
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={handleCancel}
      PaperProps={{
        sx: {
          width: {
            xs: "100%",
            sm: 420,
            md: 460,
          },

          display: "flex",
          flexDirection: "column",

          ...calendarGlassSurfaceSx,
          borderLeft: "1px solid #DCE3F1",
          background: "#FFFFFF",
          boxShadow: "-12px 0 32px rgba(54,76,132,0.12)",
        },
      }}
      slotProps={{
        backdrop: {
          sx: {
            bgcolor: "rgba(24,38,70,0.24)",
          },
        },
      }}
    >
      {/* ========================================= */}
      {/* HEADER */}
      {/* ========================================= */}

      <Box
        sx={{
          position: "relative",

          px: {
            xs: 2.25,
            sm: 2.75,
          },

          pt: {
            xs: 2.25,
            sm: 2.75,
          },

          pb: 2.25,

          flexShrink: 0,
        }}
      >
        {/* Close Button - TOP RIGHT */}

        <IconButton
          aria-label="Close filters"
          onClick={handleCancel}
          sx={{
            position: "absolute",

            top: {
              xs: 18,
              sm: 20,
            },

            right: {
              xs: 18,
              sm: 20,
            },

            width: 36,
            height: 36,

            borderRadius: "11px",

            color: "text.secondary",

            bgcolor: "#F8FAFF",

            border: "1px solid #E3E8F2",

            transition:
              "background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease",

            "&:hover": {
              bgcolor: "#F1EBFF",
              borderColor: "#D8CCFF",

              color: "#6741D9",
            },

            "&:active": {
              bgcolor: "action.selected",
            },

            "&:focus-visible": {
              outline: "2px solid",

              outlineColor: "primary.main",

              outlineOffset: 2,
            },
          }}
        >
          <CloseRoundedIcon
            sx={{
              fontSize: 22,
            }}
          />
        </IconButton>

        {/* Title */}

        <Typography
          component="h2"
          sx={{
            ...TYPOGRAPHY.sectionTitle,

            fontSize: {
              xs: "20px",
              sm: "22px",
            },

            lineHeight: {
              xs: "28px",
              sm: "30px",
            },

            pr: 6,
          }}
        >
          Filters
        </Typography>

        {/* Description */}

        <Typography
          component="p"
          sx={{
            ...TYPOGRAPHY.bodySmall,

            mt: 0.75,

            maxWidth: 340,

            color: "text.secondary",
          }}
        >
          Refine the content shown in your calendar.
        </Typography>
      </Box>

      <Divider sx={{ borderColor: "#E7EAF2" }} />

      {/* ========================================= */}
      {/* FILTER CONTENT */}
      {/* ========================================= */}

      <Box
        sx={{
          flex: 1,

          overflowY: "auto",

          px: {
            xs: 2.25,
            sm: 2.75,
          },

          py: 2.5,

          "&::-webkit-scrollbar": {
            width: 6,
          },

          "&::-webkit-scrollbar-thumb": {
            bgcolor: "#CCD5E5",

            borderRadius: 10,
          },

          "&::-webkit-scrollbar-track": {
            bgcolor: "transparent",
          },
        }}
      >
        <Stack spacing={2.25}>
          {/* Organization */}

          <CalendarFilterField
            label="Organization"
            value={filters.organization}
            options={organizations}
            placeholder="All organizations"
            onChange={(value) =>
              onFilterChange("organization", value)
            }
          />

          {/* Connected Account */}

          <CalendarFilterField
            label="Connected Account"
            value={filters.socialAccount}
            options={socialAccounts}
            placeholder="All connected accounts"
            onChange={(value) =>
              onFilterChange("socialAccount", value)
            }
          />

          {/* Content Type */}

          <CalendarFilterField
            label="Content Type"
            value={filters.contentType}
            options={contentTypes}
            placeholder="All content types"
            onChange={(value) =>
              onFilterChange("contentType", value)
            }
          />

          {/* Status */}

          <CalendarFilterField
            label="Status"
            value={filters.status}
            options={statuses}
            placeholder="All statuses"
            onChange={(value) =>
              onFilterChange("status", value)
            }
          />
        </Stack>
      </Box>

      {/* ========================================= */}
      {/* FOOTER */}
      {/* ========================================= */}

      <Divider sx={{ borderColor: "#E7EAF2" }} />

      <Box
        sx={{
          px: {
            xs: 2.25,
            sm: 2.75,
          },

          py: 2,

          flexShrink: 0,

          background: "#FFFFFF",
        }}
      >
        <Stack
          direction="row"
          spacing={1}
          justifyContent="space-between"
        >
          {/* Clear */}

          <Box
            component="button"
            type="button"
            onClick={onClear}
            sx={{
              minWidth: { xs: 96, sm: 110 },

              height: 42,

              px: 2.5,

              borderRadius: "11px",

              border: "1px solid",

              borderColor: "#D7DFF0",

              background: "#FFFFFF",
              boxShadow: "none",

              color: "text.secondary",

              cursor: "pointer",

              ...TYPOGRAPHY.button,

              transition:
                "background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease",

              "&:hover": {
                bgcolor: "#F8FAFF",
                borderColor: "#B8C7E7",

                color: "text.primary",
              },
            }}
          >
            Clear all
          </Box>

          {/* Apply */}

          <Box
            component="button"
            type="button"
            onClick={onApply}
            sx={{
              flex: 1,

              height: 42,

              px: 2.5,

              border: "1px solid transparent",

              borderRadius: "11px",

              background: "linear-gradient(105deg, #8757F3 0%, #625FF1 55%, #3689EC 100%)",
              boxShadow: "0 7px 16px rgba(92,91,219,0.18)",

              color: "primary.contrastText",

              cursor: "pointer",

              ...TYPOGRAPHY.button,

              transition:
                "background-color 0.2s ease, transform 0.15s ease",

              "&:hover": {
                background: "linear-gradient(105deg, #7948EA 0%, #5452E8 55%, #2879DF 100%)",
                boxShadow: "0 9px 20px rgba(92,91,219,0.24)",
              },

              "&:active": {
                transform: "translateY(1px)",
              },

              "&:focus-visible": {
                outline: "2px solid",

                outlineColor: "primary.main",

                outlineOffset: 2,
              },
            }}
          >
            Apply Filters
          </Box>
        </Stack>
      </Box>
    </Drawer>
  );
}
