import {
  Button,
  ButtonGroup,
} from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

const VIEW_OPTIONS = [
  {
    value: "MONTH",
    label: "Month",
  },
  {
    value: "WEEK",
    label: "Week",
  },
  {
    value: "DAY",
    label: "Day",
  },
];

export default function CalendarViewSwitcher({
  value = "MONTH",
  onChange,
}) {
  return (
    <ButtonGroup
      variant="outlined"
      sx={{
        height: 44,

        "& .MuiButton-root": {
          borderColor: "divider",
          px: {
            xs: 1.5,
            sm: 2,
          },

          ...TYPOGRAPHY.button,
        },
      }}
    >
      {VIEW_OPTIONS.map((option) => {
        const selected = value === option.value;

        return (
          <Button
            key={option.value}
            onClick={() =>
              onChange?.(option.value)
            }
            variant={
              selected
                ? "contained"
                : "outlined"
            }
            disableElevation
            sx={{
              bgcolor: selected
                ? "primary.main"
                : "background.paper",

              color: selected
                ? "primary.contrastText"
                : "text.secondary",

              borderColor: "divider",

              "&:hover": {
                bgcolor: selected
                  ? "primary.dark"
                  : "action.hover",
              },
            }}
          >
            {option.label}
          </Button>
        );
      })}
    </ButtonGroup>
  );
}