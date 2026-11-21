import LoadingState from "../../ui/LoadingState";

export default function PostLoadingState({ sx = {}, variant = "page", ...props }) {
  return (
    <LoadingState
      {...props}
      variant={variant}
      sx={{
        ...(variant === "overlay" ? {
          background: "rgba(255,255,255,.78)",
          backdropFilter: "blur(4px)",
        } : {}),
        "& p": { color: "#71809A" },
        ...sx,
      }}
    />
  );
}
