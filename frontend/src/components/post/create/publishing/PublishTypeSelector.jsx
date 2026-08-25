import {
  Box,
  Radio,
  Stack,
  Typography,
} from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";
import { useTheme } from "@mui/material/styles";

import { TYPOGRAPHY } from "../../../../theme/typography";
import { PUBLISH_TYPE_OPTIONS } from "../../../../data/publishing";

export default function PublishTypeSelector() {
  const theme = useTheme();
  const { control } = useFormContext();

  return (
    <Controller
      name="publish_type"
      control={control}
      render={({ field }) => (
        <Stack spacing={1}>
          {PUBLISH_TYPE_OPTIONS.map((option) => {
            const Icon = option.icon;

            const selected =
              field.value === option.value;

            return (
              <Box
                key={option.value}
                component="button"
                type="button"
                onClick={() =>
                  field.onChange(option.value)
                }
                sx={{
                  width: "100%",
                  minHeight: 64,

                  display: "flex",
                  alignItems: "center",

                  p: 1.25,

                  textAlign: "left",
                  cursor: "pointer",

                  border: "1px solid",
                  borderColor: selected
                    ? theme.palette.primary.main
                    : theme.palette.divider,

                  borderRadius: 2,

                  bgcolor: selected
                    ? theme.palette.action.selected
                    : theme.palette.background.paper,

                  transition:
                    "border-color 0.2s ease, background-color 0.2s ease",

                  "&:hover": {
                    borderColor:
                      theme.palette.primary.main,
                  },
                }}
              >
                <Radio
                  checked={selected}
                  tabIndex={-1}
                  disableRipple
                  sx={{
                    p: 0,
                    mr: 1,
                  }}
                />

                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    flexShrink: 0,

                    mr: 1.25,

                    borderRadius: 1.5,

                    bgcolor: selected
                      ? theme.palette.primary.main
                      : theme.palette.action.hover,

                    color: selected
                      ? theme.palette.primary.contrastText
                      : theme.palette.text.secondary,

                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Icon sx={{ fontSize: 18 }} />
                </Box>

                <Box
                  sx={{
                    minWidth: 0,
                  }}
                >
                  <Typography
                    sx={{
                      ...TYPOGRAPHY.inputLabel,
                      fontWeight: 600,
                    }}
                  >
                    {option.label}
                  </Typography>

                  <Typography
                    sx={{
                      ...TYPOGRAPHY.bodySmall,
                      fontSize: "12px",
                      lineHeight: "18px",
                    }}
                  >
                    {option.description}
                  </Typography>
                </Box>
              </Box>
            );
          })}
        </Stack>
      )}
    />
  );
}