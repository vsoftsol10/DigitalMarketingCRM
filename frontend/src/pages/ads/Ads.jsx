import {
  ArrowOutward,
  CampaignOutlined,
  Instagram,
  LanguageOutlined,
} from "@mui/icons-material";

import {
  Box,
  Button,
  Card,
  Stack,
  Typography,
} from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

const AD_PLATFORMS = [
  {
    id: "meta",
    name: "Meta Ads",
    description:
      "Create and manage campaigns across Facebook and Instagram.",
    platforms: "Facebook & Instagram",
    icon: Instagram,
    iconBackground: "#FDF2F8",
    iconColor: "#E1306C",
    url: "https://www.facebook.com/adsmanager/",
    buttonLabel: "Open Meta Ads Manager",
  },
  {
    id: "google",
    name: "Google Ads",
    description:
      "Create and manage campaigns across Google Search, Display, and YouTube.",
    platforms: "Search, Display & YouTube",
    icon: LanguageOutlined,
    iconBackground: "#EFF6FF",
    iconColor: "#2563EB",
    url: "https://ads.google.com/",
    buttonLabel: "Open Google Ads",
  },
];

function AdPlatformCard({ platform }) {
  const PlatformIcon = platform.icon;

  const handleOpenPlatform = () => {
    window.open(
      platform.url,
      "_blank",
      "noopener,noreferrer",
    );
  };

  return (
    <Card
      elevation={0}
      sx={{
        height: "100%",
        border: "1px solid #E2E8F0",
        borderRadius: "16px",
        backgroundColor: "#FFFFFF",
        overflow: "hidden",
        transition:
          "border-color 160ms ease, box-shadow 160ms ease",
        "&:hover": {
          borderColor: "#CBD5E1",
          boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
        },
      }}
    >
      <Box sx={{ p: 2.5 }}>
        <Stack spacing={2.25}>
          {/* Platform */}
          <Stack
            direction="row"
            alignItems="center"
            spacing={1.5}
          >
            <Box
              sx={{
                width: 46,
                height: 46,
                flexShrink: 0,
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor:
                  platform.iconBackground,
                color: platform.iconColor,
              }}
            >
              <PlatformIcon sx={{ fontSize: 24 }} />
            </Box>

            <Box sx={{ minWidth: 0 }}>
              <Typography
                sx={{
                  ...TYPOGRAPHY.cardTitle,
                  fontSize: "17px",
                }}
              >
                {platform.name}
              </Typography>

              <Typography
                sx={{
                  ...TYPOGRAPHY.caption,
                  mt: 0.15,
                }}
              >
                {platform.platforms}
              </Typography>
            </Box>
          </Stack>

          {/* Description */}
          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,
              lineHeight: "21px",
              maxWidth: 420,
            }}
          >
            {platform.description}
          </Typography>

          {/* Action */}
          <Button
            fullWidth
            variant="outlined"
            endIcon={<ArrowOutward sx={{ fontSize: 17 }} />}
            onClick={handleOpenPlatform}
            sx={{
              ...TYPOGRAPHY.button,
              height: 42,
              borderRadius: "10px",
              borderColor: "#CBD5E1",
              color: "#334155",
              justifyContent: "space-between",
              px: 1.75,
              textTransform: "none",
              "&:hover": {
                borderColor: "#94A3B8",
                backgroundColor: "#F8FAFC",
              },
            }}
          >
            {platform.buttonLabel}
          </Button>
        </Stack>
      </Box>
    </Card>
  );
}

export default function Ads() {
  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <Box
        sx={{
          width: "100%",
          maxWidth: 1120,
          px: {
            xs: 0,
            sm: 1,
          },
        }}
      >
        {/* Header */}
        <Box>
          <Typography sx={TYPOGRAPHY.pageTitle}>
            Ads
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.pageDescription,
              mt: 0.25,
            }}
          >
            Manage your advertising platforms and launch
            campaigns through Meta and Google Ads.
          </Typography>
        </Box>

        {/* Platform Section */}
        <Box sx={{ mt: 3.5 }}>
          <Typography sx={TYPOGRAPHY.sectionTitle}>
            Advertising Platforms
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.sectionDescription,
              mt: 0.25,
            }}
          >
            Choose the platform you want to work with.
          </Typography>
        </Box>

        {/* Cards */}
        <Box
          sx={{
            mt: 2,
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              md: "repeat(2, minmax(0, 1fr))",
            },
            gap: 2,
            alignItems: "stretch",
          }}
        >
          {AD_PLATFORMS.map((platform) => (
            <AdPlatformCard
              key={platform.id}
              platform={platform}
            />
          ))}
        </Box>

        {/* Information */}
        <Box
          sx={{
            mt: 2,
            px: 2,
            py: 1.75,
            borderRadius: "12px",
            border: "1px solid #E2E8F0",
            backgroundColor: "#F8FAFC",
          }}
        >
          <Stack
            direction="row"
            spacing={1.25}
            alignItems="flex-start"
          >
            <CampaignOutlined
              sx={{
                fontSize: 19,
                color: "#64748B",
                mt: "1px",
              }}
            />

            <Box>
              <Typography sx={TYPOGRAPHY.small}>
                Campaigns are managed on the
                advertising platforms
              </Typography>

              <Typography
                sx={{
                  ...TYPOGRAPHY.bodySmall,
                  mt: 0.2,
                }}
              >
                Use Meta Ads Manager or Google Ads to
                create campaigns, configure budgets, and
                manage advertising payments.
              </Typography>
            </Box>
          </Stack>
        </Box>
      </Box>
    </Box>
  );
}