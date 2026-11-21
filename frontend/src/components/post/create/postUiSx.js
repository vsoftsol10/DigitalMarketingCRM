export const postCardSx = {
  border: "1px solid #DDE3F1",
  borderRadius: "20px",
  background: "#FFFFFF",
  boxShadow: "0 4px 12px rgba(41,55,103,.045)",
};

export const postFormFieldSx = {
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
    "&.Mui-error fieldset, &.Mui-error .MuiOutlinedInput-notchedOutline": { borderColor: "#DC2626" },
  },
  "& .MuiFormHelperText-root.Mui-error": {
    mx: 0,
    color: "#DC2626",
    fontSize: 13,
    lineHeight: 1.45,
    overflowWrap: "anywhere",
  },
};

export const postPrimaryButtonSx = {
  minHeight: 44,
  borderRadius: "12px",
  border: "1px solid transparent",
  background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)",
  boxShadow: "0 5px 12px rgba(83,75,196,.18)",
  color: "#FFFFFF",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": {
    background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)",
    boxShadow: "0 7px 15px rgba(83,75,196,.23)",
  },
  "&:focus-visible": { outline: "2px solid #7E8FE8", outlineOffset: 3 },
  "&.Mui-disabled": { color: "rgba(255,255,255,.82)", background: "#A9A0DE", boxShadow: "none" },
};

export const postSecondaryButtonSx = {
  minHeight: 40,
  px: 1.75,
  border: "1px solid #D8DEEA",
  borderRadius: "11px",
  background: "#FFFFFF",
  boxShadow: "none",
  color: "#475569",
  textTransform: "none",
  fontSize: 13,
  fontWeight: 600,
  "&:hover": { borderColor: "#B9C4D8", background: "#F8FAFC", boxShadow: "none" },
  "&:focus-visible": { outline: "2px solid #7E8FE8", outlineOffset: 2 },
  "&.Mui-disabled": { color: "#94A3B8", borderColor: "#E5E9F1" },
};

export const postDangerButtonSx = {
  ...postSecondaryButtonSx,
  color: "#C93248",
  borderColor: "#F1C8CE",
  "&:hover": { color: "#B42336", borderColor: "#E8AAB3", background: "#FFF7F8" },
};

export const postMenuPaperSx = {
  mt: 0.75,
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

export const postAlertSx = {
  border: "1px solid #E5E9F1",
  borderRadius: "12px",
  boxShadow: "none",
  fontSize: 13,
};

export const postPickerPopupSx = {
  border: "1px solid #DDE3F1",
  borderRadius: "14px",
  background: "#FFFFFF",
  boxShadow: "0 12px 28px rgba(31,41,80,.14)",
};
