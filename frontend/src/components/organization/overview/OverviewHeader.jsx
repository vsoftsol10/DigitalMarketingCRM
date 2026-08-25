import { Box, Button, Stack, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function OverviewHeader({
  organization,
  onEdit,
  onDelete,
}) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        mb: 4,
      }}
    >
      <Box>
        {/* Back */}

        <Box
          onClick={() => navigate("/organizations")}
          sx={{
            display: "inline-flex",
            alignItems: "center",
            gap: 0.5,
            cursor: "pointer",
            color: "#64748B",
            transition: "0.2s",

            "&:hover": {
              color: "#2563EB",
            },
          }}
        >
          <ArrowBackRoundedIcon
            sx={{
              fontSize: 18,
            }}
          />

          <Typography sx={TYPOGRAPHY.breadcrumb}>
            Organizations
          </Typography>
        </Box>

        {/* Title */}

        <Typography
          sx={{
            ...TYPOGRAPHY.pageTitle,
            mt: 1.5,
          }}
        >
          {organization?.name || ""}
        </Typography>

        {/* Description */}

        <Typography
          sx={{
            ...TYPOGRAPHY.pageDescription,
            mt: 1,
            maxWidth: 720,
          }}
        >
          {organization?.description || ""}
        </Typography>
      </Box>

      <Stack
        direction="row"
        spacing={2}
      >
        <Button
          variant="outlined"
          startIcon={<EditOutlinedIcon />}
          onClick={onEdit}
          sx={{
            height: 46,
            px: 3,
            borderRadius: "14px",
            textTransform: "none",

            ...TYPOGRAPHY.formButton,

            borderColor: "#CBD5E1",
            color: "#334155",

            "&:hover": {
              borderColor: "#94A3B8",
              bgcolor: "#F8FAFC",
            },
          }}
        >
          Edit
        </Button>

        <Button
          variant="contained"
          color="error"
          startIcon={<DeleteOutlineRoundedIcon />}
          onClick={onDelete}
          sx={{
            height: 46,
            px: 3,
            borderRadius: "14px",
            textTransform: "none",

            ...TYPOGRAPHY.formButton,

            boxShadow: "none",

            "&:hover": {
              boxShadow: "none",
            },
          }}
        >
          Delete
        </Button>
      </Stack>
    </Box>
  );
}