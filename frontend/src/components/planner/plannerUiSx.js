export const plannerCardSx = {
  border: "1px solid #DDE3F1",
  borderRadius: "20px",
  background: "#FFFFFF",
  boxShadow: "0 4px 12px rgba(41,55,103,.045)",
};

export const plannerFormPaperSx = {
  width: "100%",
  minWidth: 0,
  mx: "auto",
  p: { xs: 2, sm: 3, md: 4 },
  boxSizing: "border-box",
  ...plannerCardSx,
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
    "&.Mui-error .MuiOutlinedInput-notchedOutline": { borderColor: "#DC2626" },
  },
  "& .MuiFormHelperText-root.Mui-error": {
    mt: 0.75,
    mx: 0,
    color: "#DC2626",
    fontSize: 13,
    lineHeight: 1.45,
    overflowWrap: "anywhere",
  },
};

export const plannerFormSectionSx = {
  minWidth: 0,
  p: { xs: 2, sm: 2.5 },
  border: "1px solid #E4E8F0",
  borderRadius: "16px",
  background: "#FFFFFF",
  boxShadow: "none",
};

export const plannerFormDividerSx = {
  my: { xs: 2.5, sm: 3.5 },
  borderColor: "#E5E9F1",
};

export const plannerFieldErrorInputSx = {
  "&.Mui-error .MuiOutlinedInput-notchedOutline": {
    borderColor: "#DC2626",
    borderWidth: 1,
    boxShadow: "0 0 0 2px rgba(220,38,38,.08)",
  },
};

export const plannerFieldErrorMessageSx = {
  mt: 0.75,
  mx: 0,
  color: "#DC2626",
  fontSize: 13,
  fontWeight: 500,
  lineHeight: 1.45,
  whiteSpace: "normal",
  overflowWrap: "anywhere",
};

export const plannerPrimaryButtonSx = {
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
  "&.Mui-disabled": { color: "rgba(255,255,255,.82)", background: "#A9A0DE" },
};

export const plannerSecondaryButtonSx = {
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

export const plannerDialogPaperSx = {
  borderRadius: "20px",
  overflow: "hidden",
  border: "1px solid #DDE3F1",
  background: "#FFFFFF",
  boxShadow: "0 16px 36px rgba(31,41,80,.16)",
};

export const plannerDialogTitleSx = {
  px: 3,
  py: 2.25,
  color: "#172554",
  fontSize: "1.15rem",
  lineHeight: 1.35,
  fontWeight: 700,
  background: "#FFFFFF",
  borderBottom: "1px solid #E5E9F1",
};

export const plannerDialogContentSx = {
  px: 3,
  py: 2.5,
  background: "#FFFFFF",
  "& .MuiOutlinedInput-root": { borderRadius: "12px", background: "#FFFFFF" },
};

export const plannerDialogActionsSx = {
  px: 3,
  py: 2,
  gap: 1,
  borderTop: "1px solid #E5E9F1",
  background: "#FFFFFF",
};

export const plannerDialogSecondaryButtonSx = plannerSecondaryButtonSx;

export const plannerDialogDangerButtonSx = {
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

export const plannerSelectMenuSx = {
  mt: 1,
  border: "1px solid #DDE3F1",
  borderRadius: "12px",
  background: "#FFFFFF",
  boxShadow: "0 12px 28px rgba(31,41,80,.14)",
  "& .MuiMenuItem-root": {
    minHeight: 42,
    mx: 0.75,
    my: 0.25,
    borderRadius: "9px",
    color: "#334155",
    "&:hover": { background: "#F5F2FF" },
    "&.Mui-selected": { background: "#F5F2FF", color: "#6941D9" },
  },
};

export const plannerAlertSx = {
  borderRadius: "12px",
  border: "1px solid #E5E9F1",
  boxShadow: "none",
};
