export const organizationCardSx = {
  border: "1px solid #DDE3F1",
  borderRadius: "20px",
  background: "#FFFFFF",
  boxShadow: "0 4px 12px rgba(41,55,103,.045)",
};

export const organizationFormPaperSx = {
  width: "100%",
  minWidth: 0,
  mx: "auto",
  p: { xs: 2, sm: 3, md: 4 },
  boxSizing: "border-box",
  border: "1px solid #DDE3F1",
  borderRadius: "20px",
  background: "#FFFFFF",
  boxShadow: "0 4px 12px rgba(41,55,103,.045)",
  "& .MuiOutlinedInput-root": {
    borderRadius: "12px",
    background: "#FFFFFF",
    boxShadow: "none",
    "& fieldset, & .MuiOutlinedInput-notchedOutline": { borderColor: "#DCE2EF" },
    "&:hover fieldset, &:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#B8C3D8" },
    "&.Mui-focused fieldset, &.Mui-focused .MuiOutlinedInput-notchedOutline": {
      borderColor: "#7B61E8",
      borderWidth: 1,
      boxShadow: "0 0 0 3px rgba(123,97,232,.1)",
    },
  },
};

export const organizationFormSectionSx = {
  minWidth: 0,
  p: { xs: 2, sm: 2.5 },
  border: "1px solid #E4E8F0",
  borderRadius: "16px",
  background: "#FFFFFF",
  boxShadow: "none",
};

export const organizationFormDividerSx = {
  my: { xs: 2.5, sm: 3.5 },
  borderColor: "#E5E9F1",
};

export const glassFormPaperSx = organizationFormPaperSx;
export const glassFormSectionSx = organizationFormSectionSx;
export const glassFormDividerSx = organizationFormDividerSx;

export const organizationPrimaryButtonSx = {
  borderRadius: "14px",
  border: "1px solid transparent",
  background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)",
  boxShadow: "0 5px 12px rgba(83,75,196,.18)",
  textTransform: "none",
  "&:hover": {
    background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)",
    boxShadow: "0 7px 15px rgba(83,75,196,.23)",
  },
  "&:focus-visible": { outline: "2px solid #7E8FE8", outlineOffset: 3 },
};

export const glassPrimaryButtonSx = organizationPrimaryButtonSx;

export const organizationSecondaryButtonSx = {
  minHeight: 44,
  px: 2,
  borderRadius: "12px",
  borderColor: "#D8DEEA",
  color: "#475569",
  background: "#FFFFFF",
  boxShadow: "none",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": { borderColor: "#B9C4D8", background: "#F8FAFC", boxShadow: "none" },
};

export const glassDialogPaperSx = {
  borderRadius: "20px",
  overflow: "hidden",
  border: "1px solid #DDE3F1",
  background: "#FFFFFF",
  boxShadow: "0 16px 36px rgba(31,41,80,.16)",
};

export const glassDialogTitleSx = {
  px: 3,
  py: 2.25,
  color: "#172554",
  fontSize: "1.15rem",
  lineHeight: 1.35,
  fontWeight: 700,
  background: "#FFFFFF",
  borderBottom: "1px solid #E5E9F1",
};

export const glassDialogContentSx = {
  px: 3,
  py: 2.5,
  background: "#FFFFFF",
  "&.MuiDialogContent-dividers": { borderColor: "#E5E9F1" },
  "& .MuiOutlinedInput-root": {
    borderRadius: "12px",
    background: "#FFFFFF",
    boxShadow: "none",
    "& .MuiOutlinedInput-notchedOutline": { borderColor: "#DCE2EF" },
    "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#B8C3D8" },
    "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "#7B61E8", borderWidth: 1 },
  },
  "& .MuiInputLabel-root": { color: "#64748B" },
};

export const glassDialogActionsSx = {
  px: 3,
  py: 2,
  gap: 1,
  borderTop: "1px solid #E5E9F1",
  background: "#FFFFFF",
};

export const glassDialogCardSx = {
  p: 2,
  borderRadius: "14px",
  border: "1px solid #E5E9F1",
  background: "#F8FAFC",
  boxShadow: "none",
};

export const glassDialogToggleGroupSx = {
  gap: 1,
  "& .MuiToggleButton-root": {
    flex: 1,
    minHeight: 46,
    borderRadius: "12px !important",
    border: "1px solid #DCE2EF",
    background: "#FFFFFF",
    boxShadow: "none",
    textTransform: "none",
    fontSize: 14,
    fontWeight: 600,
    color: "#475569",
  },
  "& .MuiToggleButton-root.Mui-selected": {
    color: "#6941D9",
    border: "1px solid #CFC5F8",
    background: "#F5F2FF",
    boxShadow: "none",
    "&:hover": { background: "#F5F2FF" },
  },
};

export const glassDialogSecondaryButtonSx = organizationSecondaryButtonSx;

export const glassDialogDangerButtonSx = {
  minHeight: 44,
  px: 2,
  borderRadius: "12px",
  color: "#FFFFFF",
  background: "#DC3F54",
  boxShadow: "none",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": { background: "#C93248", boxShadow: "none" },
  "&.Mui-disabled": { color: "rgba(255,255,255,.82)", background: "#E7A3AC" },
};

// Subscription dialogs use an opt-in style set so other Organization dialogs
// can retain their existing appearance.
export const subscriptionDialogPaperSx = {
  maxWidth: 560,
  maxHeight: "calc(100dvh - 32px)",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
  border: "1px solid #DDE3F1",
  borderRadius: { xs: "16px", sm: "20px" },
  background: "#FFFFFF",
  boxShadow: "0 16px 36px rgba(31,41,80,.14)",
};

export const subscriptionDialogTitleSx = {
  flexShrink: 0,
  px: { xs: 2.25, sm: 3 },
  pt: { xs: 2, sm: 2.5 },
  pb: { xs: 1.5, sm: 1.75 },
  color: "#172554",
  fontSize: { xs: "1.1rem", sm: "1.2rem" },
  lineHeight: 1.35,
  fontWeight: 700,
  background: "#FFFFFF",
  borderBottom: "1px solid #E5E9F1",
};

export const subscriptionDialogContentSx = {
  flex: "1 1 auto",
  minHeight: 0,
  overflowY: "auto",
  px: { xs: 2.25, sm: 3 },
  py: { xs: 2, sm: 2.5 },
  background: "#FFFFFF",
  "&.MuiDialogContent-dividers": { borderColor: "#E5E9F1" },
  "& .MuiOutlinedInput-root": {
    minHeight: 48,
    borderRadius: "12px",
    background: "#FFFFFF",
    boxShadow: "none",
    "& .MuiOutlinedInput-notchedOutline": { borderColor: "#DCE2EF" },
    "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#B8C3D8" },
    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
      borderColor: "#7B61E8",
      borderWidth: 1,
      boxShadow: "0 0 0 3px rgba(123,97,232,.1)",
    },
    "&.Mui-error .MuiOutlinedInput-notchedOutline": { borderColor: "#DC2626" },
    "&.Mui-disabled": { background: "#F8FAFC" },
  },
  "& .MuiInputLabel-root": { color: "#64748B" },
  "& .MuiFormHelperText-root": { mx: 0, mt: 0.75, color: "#64748B" },
  "& .MuiFormHelperText-root.Mui-error": { color: "#DC2626" },
  "& .MuiAlert-root": { borderRadius: "12px", boxShadow: "none" },
};

export const subscriptionDialogActionsSx = {
  flex: "0 0 auto",
  flexWrap: "wrap",
  justifyContent: "flex-end",
  px: { xs: 2.25, sm: 3 },
  py: { xs: 1.75, sm: 2 },
  gap: 1,
  borderTop: "1px solid #E5E9F1",
  background: "#FFFFFF",
  "& > .MuiButton-root": { minHeight: 44, width: { xs: "100%", sm: "auto" } },
};

export const subscriptionDialogCardSx = {
  p: { xs: 1.75, sm: 2 },
  border: "1px solid #E5E9F1",
  borderRadius: "14px",
  background: "#F8FAFC",
  boxShadow: "none",
};

export const subscriptionDialogToggleGroupSx = {
  gap: 1,
  "& .MuiToggleButton-root": {
    flex: "1 1 0",
    minWidth: 0,
    minHeight: 44,
    px: { xs: 1, sm: 2 },
    borderRadius: "12px !important",
    border: "1px solid #DCE2EF",
    background: "#FFFFFF",
    boxShadow: "none",
    color: "#475569",
    fontSize: 14,
    fontWeight: 600,
    textTransform: "none",
  },
  "& .MuiToggleButton-root.Mui-selected": {
    color: "#6941D9",
    borderColor: "#BFB2F4",
    background: "#F5F2FF",
    "&:hover": { background: "#F5F2FF" },
  },
};

export const subscriptionDialogSecondaryButtonSx = {
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

export const subscriptionDialogPrimaryButtonSx = {
  minHeight: 44,
  px: 2,
  borderRadius: "12px",
  color: "#FFFFFF",
  background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)",
  boxShadow: "0 5px 12px rgba(83,75,196,.18)",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": {
    background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)",
    boxShadow: "0 7px 15px rgba(83,75,196,.23)",
  },
  "&.Mui-disabled": { color: "rgba(255,255,255,.82)", background: "#A9B6D0", boxShadow: "none" },
};

export const subscriptionDialogDangerButtonSx = {
  minHeight: 44,
  px: 2,
  borderRadius: "12px",
  color: "#FFFFFF",
  background: "#D64545",
  boxShadow: "none",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": { background: "#BF3535", boxShadow: "none" },
  "&.Mui-disabled": { color: "rgba(255,255,255,.82)", background: "#E6A2A2" },
};

export const subscriptionDialogSelectSx = {
  minHeight: 48,
  borderRadius: "12px",
  background: "#FFFFFF",
};
