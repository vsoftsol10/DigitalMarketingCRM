import {
  FormControlLabel,
  Stack,
  Switch,
} from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";

export default function AIContentOptions() {
  const { control } = useFormContext();

  return (
    <Stack spacing={1}>
      <Controller
        name="ai_include_emoji"
        control={control}
        render={({ field }) => (
          <FormControlLabel
            control={
              <Switch
                checked={field.value}
                onChange={(e) =>
                  field.onChange(e.target.checked)
                }
              />
            }
            label="Include Emojis"
          />
        )}
      />

      <Controller
        name="ai_include_hashtags"
        control={control}
        render={({ field }) => (
          <FormControlLabel
            control={
              <Switch
                checked={field.value}
                onChange={(e) =>
                  field.onChange(e.target.checked)
                }
              />
            }
            label="Include Hashtags"
          />
        )}
      />

      <Controller
        name="ai_include_cta"
        control={control}
        render={({ field }) => (
          <FormControlLabel
            control={
              <Switch
                checked={field.value}
                onChange={(e) =>
                  field.onChange(e.target.checked)
                }
              />
            }
            label="Include Call To Action"
          />
        )}
      />
    </Stack>
  );
}