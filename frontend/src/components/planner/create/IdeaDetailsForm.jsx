import { Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import FormSelect from "../../ui/form/FormSelect";
import FormTextField from "../../ui/form/FormTextField";

import { PLATFORM_OPTIONS } from "../../../constants/form-options/platformOptions";

export default function IdeaDetailsForm({ organizations = [] }) {
  return (
    <FormSection
      title="Idea Details"
      description="Basic information about this content idea."
    >
      <Grid container spacing={3}>
        {/* Organization */}

        <Grid size={{ xs: 12, md: 6 }}>
          <FormSelect
            name="organization"
            label="Organization"
            required
            placeholder="Select Organization"
            options={organizations.map((organization) => ({
              value: organization.id,
              label: organization.name,
            }))}
          />
        </Grid>

        {/* Platform */}

        <Grid size={{ xs: 12, md: 6 }}>
          <FormSelect
            name="platform"
            label="Platform"
            required
            placeholder="Select Platform"
            options={PLATFORM_OPTIONS}
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="target_publish_date"
            label="Target Publish Date"
            required
            type="date"
            InputLabelProps={{
              shrink: true,
            }}
          />
        </Grid>

        {/* Title */}

        <Grid size={{ xs: 12 }}>
          <FormTextField
            name="title"
            label="Idea Title"
            required
            placeholder="Morning Coffee Routine"
          />
        </Grid>
      </Grid>
    </FormSection>
  );
}
