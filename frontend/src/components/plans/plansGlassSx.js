export const plansGlassSurfaceSx = {
  border: "1px solid #DCE3F1",
  borderRadius: { xs: "16px", sm: "18px" },
  background: "#FFFFFF",
  boxShadow: "0 8px 20px rgba(54,76,132,0.07)",
};

export const planSectionSx = {
  width: "100%",
  minWidth: 0,
  p: { xs: 1.75, sm: 2.25, md: 2.5 },
  boxSizing: "border-box",
  ...plansGlassSurfaceSx,
};

export const planInputSx = {
  "& .MuiInputLabel-root": {
    color: "#7183A1",
  },
  "& .MuiOutlinedInput-root:not(.MuiInputBase-multiline)": {
    height: 46,
    minHeight: 46,
    borderRadius: "12px",
    background: "rgba(255,255,255,0.88)",
    transition: "border-color 160ms ease, box-shadow 160ms ease",
    "& fieldset": { borderColor: "rgba(178,198,229,0.72)" },
    "&:hover fieldset": { borderColor: "#A8BCE5" },
    "&.Mui-focused": { boxShadow: "0 0 0 3px rgba(111,93,236,0.11)" },
    "&.Mui-focused fieldset": { borderColor: "#7865E8" },
    "&.Mui-disabled": { background: "#F3F5FA" },
  },
  "& .MuiOutlinedInput-input": {
    height: 46,
    boxSizing: "border-box",
  },
  "& .MuiOutlinedInput-root.MuiInputBase-multiline": {
    height: "auto",
    minHeight: 96,
    alignItems: "flex-start",
  },
  "& .MuiFormHelperText-root": { marginLeft: 0, marginTop: "5px" },
};

export const planPrimaryButtonSx = {
  minHeight: 46,
  px: 2.25,
  borderRadius: "13px",
  background: "linear-gradient(105deg, #8757F3 0%, #625FF1 55%, #3689EC 100%)",
  color: "#FFFFFF",
  fontWeight: 650,
  textTransform: "none",
  boxShadow: "0 8px 18px rgba(92,91,219,0.2)",
  "&:hover": {
    background: "linear-gradient(105deg, #7948EA 0%, #5452E8 55%, #2879DF 100%)",
    boxShadow: "0 10px 22px rgba(92,91,219,0.25)",
  },
  "&.Mui-disabled": {
    color: "#FFFFFF",
    background: "#B8B9CB",
    boxShadow: "none",
  },
};

export const planSecondaryButtonSx = {
  minHeight: 46,
  px: 2.25,
  borderRadius: "13px",
  borderColor: "#D7DFF0",
  background: "rgba(255,255,255,0.88)",
  color: "#405778",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": {
    borderColor: "#B8C7E7",
    background: "#FFFFFF",
  },
  "&.Mui-disabled": {
    borderColor: "#E2E7F1",
    color: "#A0AABD",
  },
};

export function planTone() {
  return {
    accent: "#7C3AED",
    icon: "#7C3AED",
    iconSurface: "#F1EBFF",
    surface: "#FFFFFF",
    tint: "#F8F7FF",
    border: "#DCE3F1",
  };
}
