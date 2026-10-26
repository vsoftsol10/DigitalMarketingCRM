export const plansGlassSurfaceSx = {
  border: "1px solid rgba(255,255,255,0.92)",
  borderRadius: "22px",
  background: "linear-gradient(145deg, rgba(255,255,255,0.9), rgba(233,243,255,0.82))",
  backdropFilter: "blur(16px)",
  boxShadow: "0 12px 28px rgba(70,106,172,0.12), inset 0 1px 0 rgba(255,255,255,0.98)",
};

export const planSectionSx = {
  width: "100%",
  minWidth: 0,
  p: { xs: 2, sm: 2.5, md: 3 },
  boxSizing: "border-box",
  ...plansGlassSurfaceSx,
};

export const planInputSx = {
  "& .MuiOutlinedInput-root": {
    minHeight: 52,
    borderRadius: "14px",
    background: "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(243,248,255,0.9))",
    "& fieldset": { borderColor: "rgba(178,198,229,0.72)" },
    "&:hover fieldset": { borderColor: "#AFC8F0" },
    "&.Mui-focused fieldset": { borderColor: "#79A8F6" },
  },
};

export function planTone(type) {
  const normalized = String(type || "").trim().toLowerCase();
  if (normalized === "custom") {
    return {
      accent: "#D94178",
      icon: "#E83E79",
      iconSurface: "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(255,226,237,0.86))",
      surface: "linear-gradient(145deg, rgba(255,245,249,0.96), rgba(255,226,237,0.86))",
      tint: "rgba(255,240,246,0.76)",
      border: "rgba(255,255,255,0.96)",
    };
  }
  return {
    accent: "#2679E8",
    icon: "#2787E8",
    iconSurface: "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(218,239,255,0.86))",
    surface: "linear-gradient(145deg, rgba(242,250,255,0.96), rgba(218,239,255,0.88))",
    tint: "rgba(238,248,255,0.78)",
    border: "rgba(255,255,255,0.96)",
  };
}
