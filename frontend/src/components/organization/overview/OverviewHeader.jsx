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
            px: 1.25,
            py: 0.7,
            borderRadius: "999px",
            background: "linear-gradient(145deg, rgba(255,255,255,.8), rgba(232,241,255,.68))",
            border: "1px solid rgba(255,255,255,.9)",
            boxShadow: "0 3px 9px rgba(76,102,148,.08), inset 0 1px 0 #fff",
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
          variant="contained"
          startIcon={<EditOutlinedIcon />}
          onClick={onEdit}
          sx={{
            height: 48,
            px: 2.8,
            borderRadius: "17px",
            textTransform: "none",

            ...TYPOGRAPHY.formButton,

            border: "1px solid rgba(255,255,255,.7)",
            color: "#FFFFFF",
            background: "linear-gradient(115deg, #A96BEA 0%, #7074ED 54%, #4A91ED 100%)",
            boxShadow: "0 11px 22px rgba(100,92,203,.3), 0 3px 7px rgba(65,101,210,.17), inset 0 1px 0 rgba(255,255,255,.46), inset 0 -2px 3px rgba(67,71,163,.16)",

            "&:hover": {
              background: "linear-gradient(115deg, #9D60E3 0%, #5E70E8 56%, #3D8FEA 100%)",
              boxShadow: "0 13px 24px rgba(100,92,203,.34), 0 3px 8px rgba(65,101,210,.2), inset 0 1px 0 rgba(255,255,255,.42)",
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
            height: 48,
            px: 2.8,
            borderRadius: "17px",
            textTransform: "none",

            ...TYPOGRAPHY.formButton,

            border: "1px solid rgba(255,255,255,.58)",
            background: "linear-gradient(115deg, #E65D78 0%, #D94A63 100%)",
            boxShadow: "0 10px 20px rgba(157,54,83,.22), 0 3px 7px rgba(130,42,68,.12), inset 0 1px 0 rgba(255,255,255,.48), inset 0 -2px 3px rgba(128,35,60,.12)",

            "&:hover": {
              background: "linear-gradient(115deg, #DC4D68 0%, #CB3B56 100%)",
              boxShadow: "0 12px 22px rgba(157,54,83,.27), 0 3px 8px rgba(130,42,68,.15), inset 0 1px 0 rgba(255,255,255,.48), inset 0 -2px 3px rgba(128,35,60,.14)",
            },
          }}
        >
          Delete
        </Button>
      </Stack>
    </Box>
  );
}
