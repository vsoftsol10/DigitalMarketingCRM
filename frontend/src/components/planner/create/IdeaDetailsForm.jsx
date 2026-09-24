import { Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import FormSelect from "../../ui/form/FormSelect";
import PublishAccountsField from "./PublishAccountsField";

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

        <Grid size={{ xs: 12 }}>
          <PublishAccountsField organizations={organizations} />
        </Grid>
      </Grid>
    </FormSection>
  );
}
