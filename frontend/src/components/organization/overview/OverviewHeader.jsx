import { Box, Button, Stack, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import PersonAddAlt1RoundedIcon from "@mui/icons-material/PersonAddAlt1Rounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";
import { organizationPrimaryButtonSx, organizationSecondaryButtonSx } from "../organizationUiSx";

export default function OverviewHeader({
  organization,
  onEdit,
  onInvite,
  onDelete,
}) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        gap: 2,
        mb: 4,
        flexDirection: { xs: "column", md: "row" },
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
            borderRadius: "12px",
            background: "#FFFFFF",
            border: "1px solid #DDE3F1",
            boxShadow: "none",
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
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{ width: { xs: "100%", md: "auto" }, flexWrap: "wrap" }}
      >
        <Button
          variant="contained"
          startIcon={<EditOutlinedIcon />}
          onClick={onEdit}
          sx={{
            width: { xs: "100%", sm: "auto" },
            height: 48,
            px: 2.8,
            borderRadius: "14px",
            textTransform: "none",

            ...TYPOGRAPHY.formButton,

            color: "#FFFFFF",
            ...organizationPrimaryButtonSx,

            "&:hover": {
              background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)",
              boxShadow: "0 7px 15px rgba(83,75,196,.23)",
            },
          }}
        >
          Edit
        </Button>

        <Button
          variant="outlined"
          startIcon={<PersonAddAlt1RoundedIcon />}
          onClick={onInvite}
          sx={{
            width: { xs: "100%", sm: "auto" },
            height: 48,
            px: 2.4,
            borderRadius: "12px",
            textTransform: "none",
            ...TYPOGRAPHY.formButton,
            color: "#52698B",
            ...organizationSecondaryButtonSx,
            minHeight: 48,
            "&:hover": {
              borderColor: "#B9C4D8",
              background: "#F8FAFC",
            },
          }}
        >
          Invite others to add
        </Button>

        <Button
          variant="contained"
          color="error"
          startIcon={<DeleteOutlineRoundedIcon />}
          onClick={onDelete}
          sx={{
            width: { xs: "100%", sm: "auto" },
            height: 48,
            px: 2.8,
            borderRadius: "14px",
            textTransform: "none",

            ...TYPOGRAPHY.formButton,

            background: "#DC3F54",
            boxShadow: "0 4px 10px rgba(220,63,84,.18)",

            "&:hover": {
              background: "#C93248",
              boxShadow: "0 5px 12px rgba(220,63,84,.22)",
            },
          }}
        >
          Delete
        </Button>
      </Stack>
    </Box>
  );
}
