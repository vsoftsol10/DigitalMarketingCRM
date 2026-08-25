import { Box, Divider, Typography } from "@mui/material";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import SocialPlatformCard from "../../ui/SocialPlatformCard";
import { SOCIAL_PLATFORMS } from "../../../constants/social/socialPlatforms";

export default function SocialAccountsForm() {
  return (
    <Box
      sx={{
        mt: 4,
      }}
    >
      <Typography
        sx={{
          fontSize: 18,
          fontWeight: 700,
          color: "#1E293B",
        }}
      >
        Social Accounts
      </Typography>

      <Typography
        sx={{
          mt: 0.5,
          mb: 3,
          fontSize: 15,
          color: "#64748B",
        }}
      >
        Connect the client's social media accounts. Optional — you can do this
        later from the details page.
      </Typography>

      {/* Empty State */}

      <Box
        sx={{
          height: 170,

          border: "1px dashed #D7DEE8",

          borderRadius: "18px",

          display: "flex",

          flexDirection: "column",

          alignItems: "center",

          justifyContent: "center",

          bgcolor: "#FFFFFF",
        }}
      >
        <Box
          sx={{
            width: 48,

            height: 48,

            borderRadius: "14px",

            bgcolor: "#F1F5F9",

            display: "flex",

            alignItems: "center",

            justifyContent: "center",

            mb: 2,
          }}
        >
          <ShareOutlinedIcon
            sx={{
              color: "#64748B",
            }}
          />
        </Box>

        <Typography
          sx={{
            fontSize: 17,

            fontWeight: 600,

            color: "#1E293B",
          }}
        >
          No accounts connected yet
        </Typography>

        <Typography
          sx={{
            mt: 1,

            maxWidth: 520,

            textAlign: "center",

            fontSize: 14,

            color: "#64748B",
          }}
        >
          Connect this organization's social accounts to start publishing. You
          can also do this later from the details page.
        </Typography>
      </Box>

      {/* Platforms */}

      <Typography
        sx={{
          mt: 4,

          mb: 2,

          fontSize: 15,

          fontWeight: 600,

          color: "#475569",
        }}
      >
        Connect a new account
      </Typography>

      <Box
        sx={{
          display: "flex",

          gap: 2,

          flexWrap: "wrap",
        }}
      >
        {SOCIAL_PLATFORMS.map((platform) => (
          <SocialPlatformCard
            key={platform.id}
            {...platform}
            onClick={() => console.log(platform.id)}
          />
        ))}
      </Box>

      <Divider
        sx={{
          my: 4,
        }}
      />
    </Box>
  );
}
