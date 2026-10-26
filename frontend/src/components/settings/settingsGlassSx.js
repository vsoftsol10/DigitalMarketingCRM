export const settingsGlassCardSx = {
  width: "100%",
  minWidth: 0,
  border: "1px solid rgba(255,255,255,0.94)",
  borderRadius: "24px",
  background:
    "linear-gradient(120deg, rgba(247,251,255,0.96) 0%, rgba(247,248,255,0.94) 58%, rgba(255,242,250,0.92) 100%)",
  backdropFilter: "blur(16px)",
  boxShadow:
    "0 16px 32px rgba(75,96,151,0.13), 0 3px 8px rgba(79,99,154,0.07), inset 0 1px 0 rgba(255,255,255,0.98)",
  boxSizing: "border-box",
};

export const settingsFieldSx = {
  minWidth: 0,
  "& .MuiOutlinedInput-root": {
    minHeight: 48,
    borderRadius: "12px",
    background: "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(247,250,255,0.92))",
    "& fieldset": { borderColor: "rgba(175,192,221,0.58)" },
    "&:hover fieldset": { borderColor: "rgba(123,157,218,0.72)" },
    "&.Mui-focused fieldset": { borderColor: "#7D91F3" },
    "&.Mui-disabled": { backgroundColor: "rgba(255,255,255,0.62)" },
  },
  "& .MuiInputBase-input": {
    color: "#34496D",
    minWidth: 0,
  },
  "& .MuiInputLabel-root": { color: "#7183A1" },
  "& .MuiFormHelperText-root": { ml: 0, color: "#8192AE" },
};

export const settingsPrimaryButtonSx = {
  minWidth: 136,
  height: 44,
  px: 2.5,
  borderRadius: 999,
  background: "linear-gradient(105deg, #9358F2 0%, #5578F5 58%, #2C9BEB 100%)",
  boxShadow: "0 9px 18px rgba(106,91,224,0.2), inset 0 1px 0 rgba(255,255,255,0.42)",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": {
    background: "linear-gradient(105deg, #8549E9 0%, #496AEF 58%, #228CE1 100%)",
  },
};
