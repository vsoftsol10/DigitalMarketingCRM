import { Box, Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import { plannerFieldErrorInputSx, plannerFieldErrorMessageSx, plannerFormSectionSx, plannerSelectMenuSx } from "../plannerUiSx";
import FormSelect from "../../ui/form/FormSelect";
import PublishAccountsField from "./PublishAccountsField";

export default function IdeaDetailsForm({ organizations = [] }) {
  return (
    <Box sx={plannerFormSectionSx}>
      <FormSection
        title="Idea Details"
        description="Basic information about this content idea."
        spacing={3}
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
            errorInputSx={plannerFieldErrorInputSx}
            errorMessageSx={plannerFieldErrorMessageSx}
            MenuProps={{ PaperProps: { sx: plannerSelectMenuSx } }}
          />
        </Grid>

        <Grid size={{ xs: 12 }}>
          <PublishAccountsField organizations={organizations} />
        </Grid>
        </Grid>
      </FormSection>
    </Box>
  );
}
