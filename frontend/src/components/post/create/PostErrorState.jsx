import ErrorState from "../../ui/ErrorState";
import { postCardSx, postPrimaryButtonSx } from "./postUiSx";

export default function PostErrorState({ sx = {}, ...props }) {
  return (
    <ErrorState
      {...props}
      sx={{
        "& > .MuiPaper-root": {
          ...postCardSx,
          borderRadius: "20px",
          boxShadow: "0 8px 20px rgba(41,55,103,.07)",
        },
        "& .MuiButton-contained": {
          ...postPrimaryButtonSx,
          minHeight: 42,
          borderRadius: "12px",
        },
        ...sx,
      }}
    />
  );
}
