export const settingsGlassCardSx = {
  width: "100%",
  minWidth: 0,
  border: "1px solid #DDE3F1",
  borderRadius: "20px",
  background: "#FFFFFF",
  boxShadow: "0 4px 12px rgba(41,55,103,.045)",
  boxSizing: "border-box",
};

export const settingsFieldSx = {
  minWidth: 0,
  "& .MuiOutlinedInput-root": {
    minHeight: 52,
    borderRadius: "12px",
    background: "#FFFFFF",
    "& fieldset": { borderColor: "#D8DEEA" },
    "&:hover fieldset": { borderColor: "#B8C3D8" },
    "&.Mui-focused fieldset": {
      borderColor: "#7B61E8",
      borderWidth: 1,
      boxShadow: "0 0 0 3px rgba(123,97,232,.1)",
    },
    "&.Mui-disabled": { backgroundColor: "#F8FAFC" },
  },
  "& .MuiInputBase-input": {
    color: "#334155",
    minWidth: 0,
  },
  "& .MuiInputLabel-root": { color: "#64748B" },
  "& .MuiFormHelperText-root": { ml: 0, color: "#7B8798" },
};

export const settingsPrimaryButtonSx = {
  minWidth: 136,
  minHeight: 46,
  px: 2.5,
  borderRadius: "14px",
  background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)",
  boxShadow: "0 5px 12px rgba(83,75,196,.18)",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": {
    background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)",
    boxShadow: "0 7px 15px rgba(83,75,196,.23)",
  },
  "&:focus-visible": { outline: "2px solid #7E8FE8", outlineOffset: 3 },
  "&.Mui-disabled": { color: "#FFFFFF", background: "#A9A0DE", boxShadow: "none" },
};

export const settingsSecondaryButtonSx = {
  minHeight: 40,
  px: 1.75,
  border: "1px solid #D8DEEA",
  borderRadius: "12px",
  background: "#FFFFFF",
  color: "#475569",
  boxShadow: "none",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": { borderColor: "#B9C4D8", background: "#F8FAFC", boxShadow: "none" },
  "&:focus-visible": { outline: "2px solid #7E8FE8", outlineOffset: 2 },
  "&.Mui-disabled": { color: "#94A3B8", borderColor: "#E5E9F1" },
};

export const settingsErrorAlertSx = {
  border: "1px solid #FECACA",
  borderRadius: "12px",
  background: "#FEF2F2",
  color: "#991B1B",
};
