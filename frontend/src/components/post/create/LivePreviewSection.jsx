import { Box, Paper, Typography } from "@mui/material";
import { useFormContext } from "react-hook-form";

import { TYPOGRAPHY } from "../../../theme/typography";
import { useState, useEffect } from "react";
import PreviewPlatformTabs from "./preview/PreviewPlatformTabs";
import PreviewPostCard from "./preview/PreviewPostCard";

export default function LivePreviewSection({ organizations, platforms }) {
  const { watch } = useFormContext();

  const organizationId = watch("organization");

  const organization = organizations.find((item) => item.id === organizationId);
  const selectedPlatforms = watch("platforms") || [];
  const [activePlatform, setActivePlatform] = useState("");
  const caption = watch("caption");
  const media = watch("media");

  const platform = platforms.find((item) => item.id === activePlatform);

  useEffect(() => {
    if (
      selectedPlatforms.length &&
      !selectedPlatforms.includes(activePlatform)
    ) {
      setActivePlatform(selectedPlatforms[0]);
    }
  }, [selectedPlatforms, activePlatform]);

  return (
    <Paper
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "24px",
        bgcolor: "#FFFFFF",
        overflow: "hidden",
      }}
    >
      {/* Header */}

      <Box
        sx={{
          px: 3,
          pt: 3,
          pb: 2,
          borderBottom: "1px solid #F1F5F9",
        }}
      >
        <Typography sx={TYPOGRAPHY.sectionTitle}>Live Preview</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.5,
          }}
        >
          See how your post will look before publishing.
        </Typography>
      </Box>

      {/* Platform Tabs Placeholder */}

      <PreviewPlatformTabs
        platforms={selectedPlatforms}
        value={activePlatform}
        onChange={setActivePlatform}
      />

      {/* Preview */}

      <Box
        sx={{
          p: 3,
          minHeight: 500,
          bgcolor: "#FFFFFF",
        }}
      >
        <PreviewPostCard
          organization={organization}
          platform={platform}
          caption={caption}
          media={media}
        />
      </Box>
    </Paper>
  );
}
