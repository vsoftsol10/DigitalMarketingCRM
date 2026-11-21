export const insightsGlassSurfaceSx = {
  border: "1px solid #DDE3F1",
  background: "#FFFFFF",
  boxShadow: "0 4px 12px rgba(41,55,103,.045)",
};

export const insightsGlassControlSx = {
  border: "1px solid #D8DEEA",
  background: "#FFFFFF",
  boxShadow: "none",
};

export const insightsPrimaryButtonSx = {
  minHeight: 42,
  border: "1px solid transparent",
  borderRadius: "12px",
  background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)",
  color: "#FFFFFF",
  boxShadow: "0 5px 12px rgba(83,75,196,.18)",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": {
    background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)",
    boxShadow: "0 7px 15px rgba(83,75,196,.23)",
  },
  "&:focus-visible": { outline: "2px solid #7E8FE8", outlineOffset: 3 },
  "&.Mui-disabled": { color: "#FFFFFF", background: "#A9A0DE", boxShadow: "none" },
};

export const insightsSecondaryButtonSx = {
  minHeight: 40,
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

export const insightsMenuPaperSx = {
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

export const insightsAlertSx = {
  border: "1px solid #E5E9F1",
  borderRadius: "12px",
  background: "#FFFFFF",
  boxShadow: "0 3px 10px rgba(41,55,103,.04)",
  "& .MuiAlert-action": { alignItems: "center" },
};

export const insightsEmptyCardSx = {
  border: "1px solid #DDE3F1",
  borderRadius: "20px",
  background: "#FFFFFF",
  boxShadow: "0 8px 20px rgba(41,55,103,.07)",
};
