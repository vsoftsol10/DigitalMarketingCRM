import { Box, Button } from "@mui/material";

import SaveRoundedIcon from "@mui/icons-material/SaveRounded";

import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";
import PrimaryButton from "../../ui/button/PrimaryButton";
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";

export default function UpdateOrganizationFooter({ loading = false }) {
  const navigate = useNavigate();

  return (
      <Box
        sx={{
          mt: { xs: 3, sm: 4 },
          pt: 2.5,
          borderTop: "1px solid rgba(146, 168, 201, .25)",
          display: "flex",
          justifyContent: "flex-end",
          flexDirection: { xs: "column-reverse", sm: "row" },
          alignItems: { xs: "stretch", sm: "center" },
          gap: 2,
        }}
      >
        {/* Cancel */}

        <Button
          variant="outlined"
          disabled={loading}
          onClick={() => navigate(-1)}
          sx={{
            minWidth: { xs: "100%", sm: 140 },
            height: 48,

            borderRadius: "14px",

            textTransform: "none",

            borderColor: "rgba(133, 157, 194, .5)",

            color: "#536A8A",
            background: "linear-gradient(145deg, rgba(255,255,255,.8), rgba(238,245,255,.72))",
            boxShadow: "0 3px 9px rgba(75, 101, 145, .08), inset 0 1px 0 #fff",

            ...TYPOGRAPHY.formButton,

            "&:hover": {
              borderColor: "#94A3B8",
              bgcolor: "#EEF4FF",
            },
          }}
        >
          Cancel
        </Button>

        {/* Update */}

        <PrimaryButton
          type="submit"
          loading={loading}
          fullWidth={false}
          height={48}
          startIcon={<SaveRoundedIcon />}
          sx={{
            minWidth: { xs: "100%", sm: 220 },
            textTransform: "none",
            ...TYPOGRAPHY.formButton,
            ...glassPrimaryButtonSx,
          }}
        >
          {loading ? "Saving..." : "Save Changes"}
        </PrimaryButton>
      </Box>
  );
}
