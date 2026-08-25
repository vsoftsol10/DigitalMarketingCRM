import { Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import FormTextField from "../../ui/form/FormTextField";
import FormSelect from "../../ui/form/FormSelect";
import FormTextArea from "../../ui/form/FormTextArea";

import { INDUSTRY_OPTIONS } from "../../../constants/form-options/industryOptions";

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
          <FormSelect
            name="industry"
            label="Industry"
            required
            placeholder="Select Industry"
            options={INDUSTRY_OPTIONS}
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
