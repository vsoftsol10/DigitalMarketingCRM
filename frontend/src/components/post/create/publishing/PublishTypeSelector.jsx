import {
  Box,
  Radio,
  Stack,
  Typography,
} from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";

import { TYPOGRAPHY } from "../../../../theme/typography";
import { PUBLISH_TYPE_OPTIONS } from "../../../../data/publishing";

export default function PublishTypeSelector() {
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
                  borderColor: selected ? "#C8BDF5" : "#DDE3F1",

                  borderRadius: "12px",

                  background: selected ? "#F5F2FF" : "#FFFFFF",
                  boxShadow: "none",

                  transition:
                    "border-color 0.2s ease, background-color 0.2s ease",

                  "&:hover": {
                    borderColor: "#B7A8EE",
                    bgcolor: "#FAF9FF",
                  },
                  "&:focus-visible": {
                    outline: "2px solid #7E8FE8",
                    outlineOffset: 2,
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
                    color: "#9AA7BD",
                    "&.Mui-checked": { color: "#6941D9" },
                  }}
                />

                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    flexShrink: 0,

                    mr: 1.25,

                    borderRadius: "11px",

                    background: selected ? "linear-gradient(110deg,#8B4BF5,#3977F6)" : "#F1F5F9",

                    color: selected
                      ? "#FFFFFF"
                      : "#687FAD",
                    boxShadow: "none",

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
