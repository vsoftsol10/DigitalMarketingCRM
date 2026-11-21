export const calendarGlassSurfaceSx = {
  border: "1px solid #DCE3F1",
  borderRadius: { xs: "16px", sm: "18px" },
  background: "#FFFFFF",
  boxShadow: "0 8px 20px rgba(54,76,132,0.07)",
};

export const calendarGlassControlSx = {
  border: "1px solid #D7DFF0",
  background: "#FFFFFF",
  boxShadow: "0 2px 6px rgba(54,76,132,0.04)",
  transition: "border-color 160ms ease, box-shadow 160ms ease, background-color 160ms ease",
};

export const calendarGlassInsetSx = {
  background: "#F8FAFF",
};

export const calendarPrimaryButtonSx = {
  minHeight: 44,
  borderRadius: "12px",
  background: "linear-gradient(105deg, #8757F3 0%, #625FF1 55%, #3689EC 100%)",
  color: "#FFFFFF",
  fontWeight: 650,
  textTransform: "none",
  boxShadow: "0 7px 16px rgba(92,91,219,0.18)",
  "&:hover": {
    background: "linear-gradient(105deg, #7948EA 0%, #5452E8 55%, #2879DF 100%)",
    boxShadow: "0 9px 20px rgba(92,91,219,0.24)",
  },
  "&.Mui-disabled": {
    color: "#FFFFFF",
    background: "#B8B9CB",
    boxShadow: "none",
  },
};

export const calendarSecondaryButtonSx = {
  minHeight: 42,
  borderRadius: "12px",
  borderColor: "#D7DFF0",
  background: "#FFFFFF",
  color: "#405778",
  fontWeight: 600,
  textTransform: "none",
  "&:hover": {
    borderColor: "#B8C7E7",
    background: "#F8FAFF",
  },
  "&.Mui-disabled": {
    borderColor: "#E2E7F1",
    color: "#A0AABD",
  },
};
