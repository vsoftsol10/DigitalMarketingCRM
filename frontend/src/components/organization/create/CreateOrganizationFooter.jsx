import { Box, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";
import PrimaryButton from "../../ui/button/PrimaryButton";
import { glassPrimaryButtonSx } from "../../ui/form/glassFormSx";

export default function CreateOrganizationFooter({
  loading = false,
}) {
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
      <Button
        variant="outlined"
        onClick={() => navigate("/organizations")}
        sx={{
          minWidth: { xs: "100%", sm: 140 },
          height: 48,
          borderRadius: "14px",
          textTransform: "none",
          fontSize: "15px",
          fontWeight: 600,
          borderColor: "rgba(133, 157, 194, .5)",
          color: "#536A8A",
          background: "linear-gradient(145deg, rgba(255,255,255,.8), rgba(238,245,255,.72))",
          boxShadow: "0 3px 9px rgba(75, 101, 145, .08), inset 0 1px 0 #fff",

          "&:hover": {
            borderColor: "#94A3B8",
            bgcolor: "#EEF4FF",
          },
        }}
      >
        Cancel
      </Button>

      <PrimaryButton
        type="submit"
        loading={loading}
        fullWidth={false}
        height={48}
        sx={{
          minWidth: { xs: "100%", sm: 220 },
          textTransform: "none",
          fontSize: "15px",
          fontWeight: 600,
          ...glassPrimaryButtonSx,
        }}
      >
        {loading ? "Creating..." : "Create Organization"}
      </PrimaryButton>
    </Box>
  );
}
