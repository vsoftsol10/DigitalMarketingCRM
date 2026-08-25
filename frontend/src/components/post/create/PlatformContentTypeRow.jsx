import { Box, Grid, Typography } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import ForumRoundedIcon from "@mui/icons-material/ForumRounded";
import XIcon from "@mui/icons-material/X";

import FormSelect from "../../ui/form/FormSelect";

import { TYPOGRAPHY } from "../../../theme/typography";
import { PLATFORM_COLORS } from "../../../constants/platforms/platformColors";

const PLATFORM_ICONS = {
  instagram: InstagramIcon,
  facebook: FacebookRoundedIcon,
  linkedin: LinkedInIcon,
  youtube: YouTubeIcon,
  threads: ForumRoundedIcon,
  x: XIcon,
};

function formatLabel(value) {
  return value
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function PlatformContentTypeRow({
  platform,
}) {
  const colors =
    PLATFORM_COLORS[
      platform.icon.toLowerCase()
    ];

  const Icon =
    PLATFORM_ICONS[
      platform.icon.toLowerCase()
    ];

  return (
    <Grid
      container
      spacing={3}
      alignItems="center"
    >
      {/* Left */}

      <Grid
        size={{
          xs: 12,
          md: 4,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <Box
            sx={{
              width: 42,
              height: 42,

              borderRadius: "12px",

              bgcolor: colors.iconBg,

              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Icon
              sx={{
                color: colors.iconColor,
                fontSize: 22,
              }}
            />
          </Box>

          <Typography
            sx={TYPOGRAPHY.inputLabel}
          >
            {platform.name}
          </Typography>
        </Box>
      </Grid>

      {/* Right */}

      <Grid
        size={{
          xs: 12,
          md: 8,
        }}
      >
        <FormSelect
          name={`platform_content_types.${platform.id}`}
          placeholder="Select Content Type"
          options={platform.content_types.map(
            (item) => ({
              value: item,
              label: formatLabel(item),
            })
          )}
        />
      </Grid>
    </Grid>
  );
}