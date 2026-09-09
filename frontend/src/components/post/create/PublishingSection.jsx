import { Stack } from "@mui/material";

import SectionCard from "./SectionCard";

import PublishTypeSelector from "./publishing/PublishTypeSelector";
import ScheduleFields from "./publishing/ScheduleFields";
import SchedulePreview from "./SchedulePreview";
import PublishActions from "./publishing/PublishActions";

export default function PublishingSection({ loading = false }) {
  return (
    <SectionCard
      title="Publishing"
      description="Choose when this post should be published."
    >
      <Stack spacing={2.5}>
        {/* Publish Type */}

        <PublishTypeSelector />

        {/* Schedule Fields */}

        <ScheduleFields />

        {/* Dynamic Preview */}

        <SchedulePreview />

        {/* Submit Action */}

        <PublishActions loading={loading} />
      </Stack>
    </SectionCard>
  );
}
