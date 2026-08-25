import { Grid } from "@mui/material";
import { useFormContext } from "react-hook-form";

import FormDatePicker from "../../../ui/form/FormDatePicker";
import FormTimePicker from "../../../ui/form/FormTimePicker";
import FormSelect from "../../../ui/form/FormSelect";

import { TIMEZONE_OPTIONS } from "../../../../data/publishing";

export default function ScheduleFields() {
  const { watch } = useFormContext();

  const publishType = watch("publish_type");

  if (publishType !== "SCHEDULE") {
    return null;
  }

  return (
    <Grid container spacing={1.5}>
      <Grid
        size={{
          xs: 12,
          sm: 6,
        }}
      >
        <FormDatePicker
          name="publish_date"
          label="Publish Date"
          required
          compact
        />
      </Grid>

      <Grid
        size={{
          xs: 12,
          sm: 6,
        }}
      >
        <FormTimePicker
          name="publish_time"
          label="Publish Time"
          required
          compact
        />
      </Grid>

      <Grid size={12}>
        <FormSelect
          name="timezone"
          label="Timezone"
          required
          compact
          options={TIMEZONE_OPTIONS}
        />
      </Grid>
    </Grid>
  );
}
