import { Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import FormTextField from "../../ui/form/FormTextField";

export default function PrimaryContactForm() {
  return (
    <FormSection
      title="Primary Contact"
      description="Primary contact person for this organization."
    >
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="contact_name"
            label="Contact Name"
            required
            placeholder="John Doe"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="contact_email"
            label="Email Address"
            required
            type="email"
            placeholder="john@company.com"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="contact_phone"
            label="Phone Number"
            type="tel"
            placeholder="+91 9876543210"
          />
        </Grid>
      </Grid>
    </FormSection>
  );
}
