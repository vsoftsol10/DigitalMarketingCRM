import EmptyState from "../ui/EmptyState";
import { plannerCardSx, plannerPrimaryButtonSx } from "./plannerUiSx";

export default function PlannerEmptyState({ sx = {}, ...props }) {
  return (
    <EmptyState
      {...props}
      sx={{
        "& > .MuiPaper-root": {
          ...plannerCardSx,
          borderRadius: "20px",
          boxShadow: "0 8px 20px rgba(41,55,103,.07)",
        },
        "& .MuiButton-contained": {
          ...plannerPrimaryButtonSx,
          minHeight: 42,
          borderRadius: "12px",
        },
        ...sx,
      }}
    />
  );
}
