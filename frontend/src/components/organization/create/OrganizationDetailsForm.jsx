import { Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import FormTextField from "../../ui/form/FormTextField";
import FormTextArea from "../../ui/form/FormTextArea";

export default function OrganizationDetailsForm() {
  return (
    <FormSection
      title="Organization Details"
      description="The basic information about this organization."
    >
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="name"
            label="Organization Name"
            required
            placeholder="Lumen Coffee Co."
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="industry"
            label="Industry"
            required
            placeholder="Enter industry"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="website"
            label="Website"
            placeholder="https://example.com"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="location"
            label="Location"
            placeholder="Chennai, Tamil Nadu"
          />
        </Grid>

        <Grid size={{ xs: 12 }}>
          <FormTextArea
            name="description"
            label="Description"
            placeholder="Write a short description about the organization..."
            rows={4}
          />
        </Grid>
      </Grid>
    </FormSection>
  );
}
