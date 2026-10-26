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
          background: "linear-gradient(155deg, rgba(250,253,255,0.99) 0%, rgba(231,241,255,0.98) 100%)",
          boxShadow: "-18px 0 48px rgba(56,89,147,0.2), inset 1px 0 0 rgba(255,255,255,0.96)",
        },
      }}
      slotProps={{
        backdrop: {
          sx: {
            bgcolor: "rgba(58, 81, 119, 0.28)",
            backdropFilter: "blur(4px)",
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
            xs: 3,
            sm: 3.5,
          },

          pt: {
            xs: 3,
            sm: 3.5,
          },

          pb: 3,

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

            width: 40,
            height: 40,

            borderRadius: "50%",

            color: "text.secondary",

            bgcolor: "rgba(255,255,255,0.52)",

            border: "1px solid transparent",

            transition:
              "background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease",

            "&:hover": {
              bgcolor: "rgba(220,235,255,0.92)",
              borderColor: "rgba(186,207,242,0.9)",

              color: "text.primary",
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

      <Divider sx={{ borderColor: "rgba(190,211,242,0.68)" }} />

      {/* ========================================= */}
      {/* FILTER CONTENT */}
      {/* ========================================= */}

      <Box
        sx={{
          flex: 1,

          overflowY: "auto",

          px: {
            xs: 3,
            sm: 3.5,
          },

          py: 3.5,

          "&::-webkit-scrollbar": {
            width: 6,
          },

          "&::-webkit-scrollbar-thumb": {
            bgcolor: "rgba(142,170,211,0.45)",

            borderRadius: 10,
          },

          "&::-webkit-scrollbar-track": {
            bgcolor: "transparent",
          },
        }}
      >
        <Stack spacing={3}>
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

      <Divider sx={{ borderColor: "rgba(190,211,242,0.68)" }} />

      <Box
        sx={{
          px: {
            xs: 3,
            sm: 3.5,
          },

          py: 2.5,

          flexShrink: 0,

          background: "linear-gradient(180deg, rgba(247,251,255,0.98), rgba(231,241,255,0.97))",
        }}
      >
        <Stack
          direction="row"
          spacing={1.5}
          justifyContent="space-between"
        >
          {/* Clear */}

          <Box
            component="button"
            type="button"
            onClick={onClear}
            sx={{
              minWidth: 110,

              height: 44,

              px: 2.5,

              borderRadius: 2,

              border: "1px solid",

              borderColor: "rgba(194,214,246,0.86)",

              background: "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(232,242,255,0.9))",
              boxShadow: "0 4px 10px rgba(70,106,172,0.09), inset 0 1px 0 #FFFFFF",

              color: "text.secondary",

              cursor: "pointer",

              ...TYPOGRAPHY.button,

              transition:
                "background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease",

              "&:hover": {
                bgcolor: "rgba(220,235,255,0.92)",
                borderColor: "#AFC8F0",

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

              height: 44,

              px: 2.5,

              border: "1px solid rgba(255,255,255,0.8)",

              borderRadius: 999,

              background: "linear-gradient(105deg, #9872ED 0%, #5D86EA 60%, #39AFE0 100%)",
              boxShadow: "0 7px 16px rgba(78,112,207,0.25), inset 0 1px 0 rgba(255,255,255,0.38)",

              color: "primary.contrastText",

              cursor: "pointer",

              ...TYPOGRAPHY.button,

              transition:
                "background-color 0.2s ease, transform 0.15s ease",

              "&:hover": {
                background: "linear-gradient(105deg, #875EE0 0%, #4F76DE 60%, #2A9FD0 100%)",
                boxShadow: "0 10px 20px rgba(78,112,207,0.32)",
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
