const CRM_PRIMARY = "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)";
const CRM_PRIMARY_HOVER = "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)";

export const socialDialogPaperSx = {
  maxWidth: 600,
  maxHeight: "calc(100dvh - 32px)",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  border: "1px solid #DDE3F1",
  borderRadius: { xs: "16px", sm: "20px" },
  background: "#FFFFFF",
  boxShadow: "0 16px 36px rgba(31,41,80,.14)",
};

export const socialDialogTitleSx = {
  flexShrink: 0,
  display: "flex",
  alignItems: "center",
  gap: 1.5,
  px: { xs: 2.25, sm: 3 },
  py: { xs: 1.75, sm: 2.25 },
  color: "#172554",
  fontSize: { xs: "1.05rem", sm: "1.15rem" },
  lineHeight: 1.35,
  fontWeight: 700,
  background: "#FFFFFF",
  borderBottom: "1px solid #E5E9F1",
};

export const socialDialogContentSx = {
  flex: "1 1 auto",
  minHeight: 0,
  overflowY: "auto",
  px: { xs: 2.25, sm: 3 },
  py: { xs: 2, sm: 2.5 },
  background: "#FFFFFF",
  "&.MuiDialogContent-dividers": { borderColor: "#E5E9F1" },
  "& .MuiAlert-root": {
    borderRadius: "12px",
    boxShadow: "none",
    alignItems: "flex-start",
    "& .MuiAlert-message": { minWidth: 0, overflowWrap: "anywhere" },
  },
};

export const socialDialogActionsSx = {
  flex: "0 0 auto",
  display: "flex",
  flexWrap: "wrap",
  justifyContent: "flex-end",
  px: { xs: 2.25, sm: 3 },
  py: { xs: 1.75, sm: 2 },
  gap: 1,
  borderTop: "1px solid #E5E9F1",
  background: "#FFFFFF",
  "& > .MuiButton-root": {
    minHeight: 44,
    width: { xs: "100%", sm: "auto" },
    maxWidth: "100%",
    whiteSpace: "normal",
  },
};

export const socialDialogRequirementCardSx = {
  display: "flex",
  alignItems: "flex-start",
  gap: { xs: 1.25, sm: 1.5 },
  p: { xs: 1.25, sm: 1.5 },
  border: "1px solid #E5E9F1",
  borderRadius: "14px",
  background: "#FFFFFF",
  boxShadow: "0 2px 8px rgba(41,55,103,.035)",
};

export const socialDialogNumberSx = {
  width: 28,
  height: 28,
  minWidth: 28,
  borderRadius: "50%",
  display: "grid",
  placeItems: "center",
  background: "#F1EDFF",
  color: "#6941D9",
  fontSize: "0.75rem",
  fontWeight: 700,
};

export const socialDialogInfoSx = {
  mt: 2.5,
  px: { xs: 1.5, sm: 2 },
  py: 1.5,
  border: "1px solid #E2E8F0",
  borderRadius: "12px",
  background: "#F8FAFC",
  color: "#475569",
  boxShadow: "none",
};

export const socialDialogReconnectInfoSx = {
  ...socialDialogInfoSx,
  borderColor: "#F3E3C2",
  background: "#FFFCF5",
};

export const socialDialogSecondaryButtonSx = {
  minHeight: 44,
  px: 2,
  border: "1px solid #D8DEEA",
  borderRadius: "12px",
  color: "#475569",
  background: "#FFFFFF",
  boxShadow: "none",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": { borderColor: "#B9C4D8", background: "#F8FAFC", boxShadow: "none" },
  "&.Mui-disabled": { borderColor: "#E2E8F0", color: "#94A3B8" },
};

export const socialDialogPrimaryButtonSx = {
  minHeight: 44,
  px: 2,
  borderRadius: "12px",
  color: "#FFFFFF",
  background: CRM_PRIMARY,
  boxShadow: "0 5px 12px rgba(83,75,196,.18)",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": { background: CRM_PRIMARY_HOVER, boxShadow: "0 7px 15px rgba(83,75,196,.23)" },
  "&.Mui-disabled": { color: "rgba(255,255,255,.82)", background: "#A9B6D0", boxShadow: "none" },
};

export const socialDialogFacebookIconTileSx = {
  width: 38,
  height: 38,
  flex: "0 0 auto",
  display: "grid",
  placeItems: "center",
  border: "1px solid #D7E7FF",
  borderRadius: "12px",
  background: "#EFF6FF",
  color: "#1877F2",
  "& svg": { fontSize: 22 },
};

export const socialDialogInstagramIconTileSx = {
  ...socialDialogFacebookIconTileSx,
  borderColor: "#FAD7E8",
  background: "#FFF1F7",
  color: "#D62976",
};

export const socialPageRowSx = (connected) => ({
  display: "flex",
  alignItems: { xs: "flex-start", sm: "center" },
  gap: { xs: 1.25, sm: 1.5 },
  flexWrap: { xs: "wrap", sm: "nowrap" },
  px: { xs: 1.25, sm: 1.75 },
  py: { xs: 1.25, sm: 1.5 },
  border: "1px solid",
  borderColor: connected ? "#B9E6CC" : "#E2E8F0",
  borderRadius: "14px",
  background: connected ? "#FBFEFC" : "#FFFFFF",
  boxShadow: "none",
  "& .MuiListItemText-primary": {
    color: "#172554",
    fontSize: 14,
    lineHeight: 1.4,
    fontWeight: 600,
    overflowWrap: "anywhere",
  },
  "& .MuiListItemText-secondary": {
    mt: 0.35,
    color: "#64748B",
    fontSize: 12,
    lineHeight: 1.45,
    overflowWrap: "anywhere",
  },
});

export const socialPageConnectedButtonSx = {
  minHeight: 40,
  borderColor: "#B7E4C7",
  borderRadius: "11px",
  color: "#15803D",
  background: "#F0FDF4",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": { borderColor: "#86D3A3", background: "#F0FDF4" },
};
