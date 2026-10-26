import { Box, Button, Stack, Typography } from "@mui/material";

import ArrowBackOutlinedIcon from "@mui/icons-material/ArrowBackOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";

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
        direction="row"
        alignItems="flex-start"
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
            ml: "auto",
            flexShrink: 0,
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
              minWidth: 114,
              height: 46,

              px: 2,

              borderRadius: 999,

              border: "1px solid rgba(255,255,255,0.96)",

              background: "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(234,243,255,0.84))",

              color: "#30466A",

              fontSize: "14px",
              fontWeight: 500,
              lineHeight: "20px",

              textTransform: "none",

              whiteSpace: "nowrap",

              "&:hover": {
                borderColor: "#B9CEF0",
                background: "linear-gradient(145deg, #FFFFFF, #EAF3FF)",
              },
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
              minWidth: 100,
              height: 46,

              px: 2,

              borderRadius: 999,

              border: "1px solid rgba(255,255,255,0.96)",

              background: "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(234,243,255,0.84))",

              color: "#30466A",

              fontSize: "14px",
              fontWeight: 500,
              lineHeight: "20px",

              textTransform: "none",

              whiteSpace: "nowrap",

              "&:hover": {
                borderColor: "#B9CEF0",
                background: "linear-gradient(145deg, #FFFFFF, #EAF3FF)",
              },
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
            </Button>
          )}
        </Stack>
      </Stack>
    </Box>
  );
}
