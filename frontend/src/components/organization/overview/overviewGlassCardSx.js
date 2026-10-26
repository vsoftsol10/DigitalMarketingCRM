const overviewGlassCardSx = {
  position: "relative",
  overflow: "hidden",
  border: "1px solid rgba(255,255,255,.9)",
  borderRadius: "24px",
  background:
    "linear-gradient(145deg, rgba(250,252,255,.98) 0%, rgba(242,247,255,.96) 58%, rgba(237,244,255,.92) 100%)",
  boxShadow:
    "0 16px 30px rgba(75,96,151,.14), 0 3px 8px rgba(79,99,154,.09), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -2px 5px rgba(112,127,177,.08)",
  backdropFilter: "blur(16px)",
  "&::before": {
    content: '""',
    position: "absolute",
    inset: 4,
    borderRadius: "20px",
    border: "1px solid rgba(255,255,255,.78)",
    pointerEvents: "none",
  },
};

export default overviewGlassCardSx;
