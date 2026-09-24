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

          bgcolor: "background.paper",

          boxShadow: "0 20px 60px rgba(15, 23, 42, 0.16)",
        },
      }}
      slotProps={{
        backdrop: {
          sx: {
            bgcolor: "rgba(15, 23, 42, 0.42)",
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

            borderRadius: 2,

            color: "text.secondary",

            bgcolor: "transparent",

            border: "1px solid transparent",

            transition:
              "background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease",

            "&:hover": {
              bgcolor: "action.hover",

              borderColor: "divider",

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

      <Divider />

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
            bgcolor: "divider",

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

      <Divider />

      <Box
        sx={{
          px: {
            xs: 3,
            sm: 3.5,
          },

          py: 2.5,

          flexShrink: 0,

          bgcolor: "background.paper",
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

              borderColor: "divider",

              bgcolor: "background.paper",

              color: "text.secondary",

              cursor: "pointer",

              ...TYPOGRAPHY.button,

              transition:
                "background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease",

              "&:hover": {
                bgcolor: "action.hover",

                borderColor: "text.secondary",

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

              border: "none",

              borderRadius: 2,

              bgcolor: "primary.main",

              color: "primary.contrastText",

              cursor: "pointer",

              ...TYPOGRAPHY.button,

              transition:
                "background-color 0.2s ease, transform 0.15s ease",

              "&:hover": {
                bgcolor: "primary.dark",
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
