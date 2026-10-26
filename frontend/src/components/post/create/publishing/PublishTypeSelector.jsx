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
                  borderColor: selected
                    ? "rgba(131,145,226,.72)"
                    : "rgba(255,255,255,.92)",

                  borderRadius: "14px",

                  background: selected
                    ? "linear-gradient(145deg, rgba(238,241,255,.94), rgba(225,234,255,.82))"
                    : "linear-gradient(145deg, rgba(250,252,255,.88), rgba(239,245,255,.76))",
                  boxShadow: selected
                    ? "0 5px 12px rgba(91,105,174,.12), inset 0 2px 0 rgba(255,255,255,.95)"
                    : "inset 0 1px 0 rgba(255,255,255,.95)",

                  transition:
                    "border-color 0.2s ease, background-color 0.2s ease",

                  "&:hover": {
                    borderColor:
                      "rgba(131,145,226,.72)",
                    bgcolor: "rgba(237,243,255,.9)",
                  },
                  "&:focus-visible": {
                    outline: "2px solid rgba(126,143,232,.72)",
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
                  }}
                />

                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    flexShrink: 0,

                    mr: 1.25,

                    borderRadius: "11px",

                    background: selected
                      ? "linear-gradient(145deg, #8E78E8, #628BEA)"
                      : "linear-gradient(145deg, rgba(255,255,255,.94), rgba(224,235,255,.82))",

                    color: selected
                      ? "#FFFFFF"
                      : "#687FAD",
                    boxShadow:
                      "0 3px 7px rgba(82,101,159,.12), inset 0 1px 0 rgba(255,255,255,.88)",

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
