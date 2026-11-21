import AddRoundedIcon from "@mui/icons-material/AddRounded";
import BusinessRoundedIcon from "@mui/icons-material/BusinessRounded";
import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

const ORGANIZATION_CREATE_PATH = "/organizations/new";
const ORGANIZATION_DESCRIPTION = "You haven't created any organizations yet. "
  + "Create an organization to start managing your social media content.";

export default function OrganizationRequiredEmptyState({ onAction }) {
  const navigate = useNavigate();
  const handleCreateOrganization = onAction || (() => navigate(ORGANIZATION_CREATE_PATH));

  return (
    <Box
      component="section"
      role="status"
      aria-label="Create Your First Organization"
      sx={{
        width: "100%",
        minHeight: "calc(100dvh - 144px)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        px: { xs: 2, sm: 3 },
        py: 2,
        textAlign: "center",
      }}
    >
      <Box
        sx={{
          width: "100%",
          maxWidth: 640,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <Box
          aria-hidden="true"
          sx={{
            width: 108,
            height: 108,
            mb: 3.75,
            position: "relative",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            "&::after": {
              content: '""',
              position: "absolute",
              left: "50%",
              bottom: 3,
              width: 99,
              height: 10,
              transform: "translateX(-50%)",
              borderRadius: "50%",
              background: "rgba(126, 87, 245, 0.13)",
              filter: "blur(1px)",
            },
          }}
        >
          <Box
            sx={{
              width: { xs: 76, sm: 90 },
              height: { xs: 76, sm: 90 },
              zIndex: 1,
              display: "grid",
              placeItems: "center",
              border: "1px solid #E5DCFF",
              borderRadius: { xs: "18px", sm: "22px" },
              color: "#7047E8",
              background: "linear-gradient(145deg, #FFFFFF 0%, #F1EBFF 100%)",
              boxShadow: "0 7px 16px rgba(103, 65, 217, 0.1)",
              "& svg": { fontSize: { xs: 41, sm: 49 } },
            }}
          >
            <BusinessRoundedIcon />
          </Box>
          <Box
            sx={{
              position: "absolute",
              top: 0,
              right: 0,
              width: 34,
              height: 30,
              color: "#8658F4",
              "& span": {
                position: "absolute",
                display: "block",
                borderRadius: 99,
                background: "currentColor",
              },
              "& span:nth-of-type(1)": { top: 0, left: 4, width: 5, height: 14 },
              "& span:nth-of-type(2)": { top: 10, left: 21, width: 5, height: 12, transform: "rotate(42deg)" },
              "& span:nth-of-type(3)": { top: 23, left: 24, width: 12, height: 5 },
            }}
          >
            <Box component="span" />
            <Box component="span" />
            <Box component="span" />
          </Box>
        </Box>
        <Typography
          component="h2"
          sx={{
            color: "#17294D",
            fontWeight: 700,
            mb: 2,
            fontSize: { xs: 22, sm: 25, md: 27 },
            lineHeight: 1.25,
            textWrap: "balance",
          }}
        >
          Create Your First Organization
        </Typography>
        <Typography
          sx={{
            maxWidth: 600,
            color: "#64748B",
            fontSize: { xs: 14, sm: 16 },
            lineHeight: 1.5,
            textWrap: "balance",
          }}
        >
          {ORGANIZATION_DESCRIPTION}
        </Typography>
        <Button
          variant="contained"
          onClick={handleCreateOrganization}
          startIcon={<AddRoundedIcon />}
          sx={{
            mt: 3.25,
            width: { xs: "100%", sm: 305 },
            maxWidth: "100%",
            minWidth: 0,
            minHeight: 49,
            flex: "0 0 auto",
            alignSelf: "center",
            px: { xs: 1.75, sm: 2.75 },
            borderRadius: "12px",
            color: "#FFFFFF",
            background: "linear-gradient(105deg, #8757F3 0%, #625FF1 55%, #3689EC 100%)",
            boxShadow: "0 7px 16px rgba(92, 91, 219, 0.2)",
            fontSize: 14.5,
            fontWeight: 700,
            textTransform: "none",
            "& .MuiButton-startIcon svg": { fontSize: 18 },
            "&:hover": {
              background: "linear-gradient(105deg, #7948EA 0%, #5452E8 55%, #2879DF 100%)",
              boxShadow: "0 9px 19px rgba(92, 91, 219, 0.24)",
            },
          }}
        >
          Create Organization
        </Button>
      </Box>
    </Box>
  );
}
