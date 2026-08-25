import { Box, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function CreateOrganizationFooter({
  loading = false,
}) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        mt: 5,
        pt: 3,
        borderTop: "1px solid #E2E8F0",

        display: "flex",
        justifyContent: "flex-end",
        gap: 2,
      }}
    >
      <Button
        variant="outlined"
        onClick={() => navigate("/organizations")}
        sx={{
          minWidth: 140,
          height: 48,
          borderRadius: "14px",
          textTransform: "none",
          fontSize: "15px",
          fontWeight: 600,
          borderColor: "#CBD5E1",
          color: "#475569",

          "&:hover": {
            borderColor: "#94A3B8",
            bgcolor: "#F8FAFC",
          },
        }}
      >
        Cancel
      </Button>

      <Button
        type="submit"
        variant="contained"
        disabled={loading}
        sx={{
          minWidth: 220,
          height: 48,
          borderRadius: "14px",
          textTransform: "none",
          fontSize: "15px",
          fontWeight: 600,
          boxShadow: "none",

          "&:hover": {
            boxShadow: "none",
          },
        }}
      >
        {loading
          ? "Creating..."
          : "Create Organization"}
      </Button>
    </Box>
  );
}