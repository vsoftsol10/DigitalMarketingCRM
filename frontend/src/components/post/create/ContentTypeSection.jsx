import { Stack } from "@mui/material";
import { useFormContext } from "react-hook-form";

import SectionCard from "./SectionCard";
import PlatformContentTypeRow from "./PlatformContentTypeRow";

export default function ContentTypeSection({
  platforms = [],
}) {
  const { watch } =
    useFormContext();

  const selectedPlatforms =
    watch("platforms") || [];

  const activePlatforms =
    platforms.filter((platform) =>
      selectedPlatforms.includes(
        platform.id
      )
    );

  if (activePlatforms.length === 0) {
    return null;
  }

  return (
    <SectionCard
      title="Content Type"
      description="Choose the content type for each selected platform."
    >
      <Stack spacing={3}>
        {activePlatforms.map(
          (platform) => (
            <PlatformContentTypeRow
              key={platform.id}
              platform={platform}
            />
          )
        )}
      </Stack>
    </SectionCard>
  );
}