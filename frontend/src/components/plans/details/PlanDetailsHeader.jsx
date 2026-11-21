import { Box, Button, Stack, Typography } from "@mui/material";

import ArrowBackOutlinedIcon from "@mui/icons-material/ArrowBackOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import { planSecondaryButtonSx } from "../plansGlassSx";

export default function PlanDetailsHeader({ plan, onBack, onEdit, onDelete }) {
  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        boxSizing: "border-box",
      }}
    >
      <Stack
        direction={{ xs: "column", md: "row" }}
        alignItems={{ xs: "stretch", md: "center" }}
        spacing={{ xs: 1.5, md: 0 }}
        sx={{
          width: "100%",
          minWidth: 0,
        }}
      >
        {/* =========================
            LEFT — PLAN INFORMATION
        ========================= */}

        <Box
          sx={{
            minWidth: 0,
            flex: 1,
          }}
        >
          <Typography
            component="h1"
            sx={{
              fontSize: "28px",
              fontWeight: 700,
              lineHeight: "34px",
              letterSpacing: "-0.02em",
              color: "#12264D",

              m: 0,

              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {plan.name}
          </Typography>

          <Typography
            component="p"
            sx={{
              fontSize: "14px",
              fontWeight: 400,
              lineHeight: "20px",
              color: "#94A3B8",

              mt: 0.35,
              mb: 0,
            }}
          >
            {plan.type}
          </Typography>
        </Box>

        {/* =========================
            RIGHT — ACTION BUTTONS
        ========================= */}

        <Stack
          direction="row"
          alignItems="center"
          spacing={1}
          sx={{
            ml: { xs: 0, md: "auto" },
            flexShrink: 0,
            width: { xs: "100%", md: "auto" },
            flexWrap: { xs: "wrap", sm: "nowrap" },
            "& > .MuiButton-root": { flex: { xs: "1 1 105px", md: "0 0 auto" } },
          }}
        >
          {/* BACK */}

          <Button
            type="button"
            variant="outlined"
            startIcon={
              <ArrowBackOutlinedIcon
                sx={{
                  fontSize: 18,
                }}
              />
            }
            onClick={onBack}
            sx={{
              ...planSecondaryButtonSx,
              minWidth: 104,
              minHeight: 44,
              whiteSpace: "nowrap",
            }}
          >
            Back
          </Button>

          {/* EDIT */}

          <Button
            type="button"
            variant="outlined"
            startIcon={
              <EditOutlinedIcon
                sx={{
                  fontSize: 18,
                }}
              />
            }
            onClick={onEdit}
            sx={{
              ...planSecondaryButtonSx,
              minWidth: 100,
              minHeight: 44,
              whiteSpace: "nowrap",
            }}
          >
            Edit
          </Button>

          {/* DELETE */}

          {/* <Button
            type="button"
            variant="contained"
            disableElevation
            startIcon={
              <DeleteOutlineOutlinedIcon
                sx={{
                  fontSize: 18,
                }}
              />
            }
            onClick={onDelete}
            sx={{
              minWidth: 120,
              height: 46,

              px: 2,

              borderRadius: "14px",

              backgroundColor: "#DC2626",

              color: "#FFFFFF",

              fontSize: "14px",
              fontWeight: 600,
              lineHeight: "20px",

              textTransform: "none",

              whiteSpace: "nowrap",

              "&:hover": {
                backgroundColor: "#B91C1C",
              },
            }}
          >
            Delete
          </Button> */}
          {!plan.is_system && (
            <Button
              type="button"
              variant="contained"
              disableElevation
              startIcon={
                <DeleteOutlineOutlinedIcon
                  sx={{
                    fontSize: 18,
                  }}
                />
              }
              onClick={onDelete}
              sx={{
                minWidth: 110,
                minHeight: 44,
                px: 2,
                borderRadius: "13px",

                backgroundColor: "#DC2626",

                color: "#FFFFFF",

                fontSize: "14px",
                fontWeight: 600,
                lineHeight: "20px",

                textTransform: "none",

                whiteSpace: "nowrap",

                "&:hover": {
                  backgroundColor: "#B91C1C",
                },
              }}
            >
              Delete
            </Button>
          )}
        </Stack>
      </Stack>
    </Box>
  );
}
