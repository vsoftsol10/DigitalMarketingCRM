export const glassDialogPaperSx = {
  borderRadius: "24px",
  overflow: "hidden",
  border: "1px solid rgba(255,255,255,.96)",
  background:
    "radial-gradient(ellipse at 100% 0%, rgba(232,216,255,.2), transparent 35%), linear-gradient(145deg, rgba(255,255,255,.98), rgba(238,245,255,.94) 56%, rgba(249,243,255,.92))",
  boxShadow:
    "0 18px 44px rgba(55,77,119,.2), 0 4px 12px rgba(82,103,154,.08), inset 0 1px 0 rgba(255,255,255,.98)",
  backdropFilter: "blur(18px)",
};

export const glassDialogTitleSx = {
  px: 3,
  py: 2.5,
  color: "#17294D",
  fontSize: "1.2rem",
  lineHeight: 1.35,
  fontWeight: 700,
  background:
    "linear-gradient(145deg, rgba(235,243,255,.9), rgba(255,255,255,.82))",
  borderBottom: "1px solid rgba(146,168,201,.22)",
};

export const glassDialogContentSx = {
  px: 3,
  py: 3,
  background:
    "linear-gradient(180deg, rgba(248,251,255,.72), rgba(255,255,255,.5))",
  "&.MuiDialogContent-dividers": {
    borderTop: "1px solid rgba(146,168,201,.22)",
    borderBottom: "1px solid rgba(146,168,201,.22)",
  },
  "& .MuiOutlinedInput-root": {
    borderRadius: "14px",
    background:
      "linear-gradient(145deg, rgba(232,241,255,.78), rgba(255,255,255,.94) 58%, rgba(246,244,255,.84))",
    boxShadow:
      "inset 0 2px 5px rgba(77,102,145,.06), inset 0 1px 0 rgba(255,255,255,.96), 0 4px 10px rgba(79,102,153,.06)",
    "& .MuiOutlinedInput-notchedOutline": {
      borderColor: "rgba(142,164,204,.38)",
    },
    "&:hover .MuiOutlinedInput-notchedOutline": {
      borderColor: "rgba(135,158,211,.78)",
    },
    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
      borderColor: "#7D96D4",
      borderWidth: 1,
      boxShadow: "0 0 0 3px rgba(125,150,212,.13)",
    },
  },
  "& .MuiInputLabel-root": {
    color: "#657899",
  },
};

export const glassDialogActionsSx = {
  px: 3,
  py: 2.25,
  gap: 1,
  borderTop: "1px solid rgba(146,168,201,.2)",
  background: "rgba(240,246,255,.66)",
};

export const glassDialogCardSx = {
  p: 2,
  borderRadius: "16px",
  border: "1px solid rgba(255,255,255,.96)",
  background:
    "linear-gradient(145deg, rgba(239,246,255,.84), rgba(255,255,255,.78) 58%, rgba(249,243,255,.72))",
  boxShadow:
    "0 7px 16px rgba(73,99,153,.08), inset 0 1px 0 rgba(255,255,255,.98), inset 0 -1px 0 rgba(121,145,189,.08)",
};

export const glassDialogToggleGroupSx = {
  gap: 1,
  "& .MuiToggleButton-root": {
    flex: 1,
    minHeight: 48,
    borderRadius: "12px !important",
    border: "1px solid rgba(173,193,226,.58)",
    background:
      "linear-gradient(145deg, rgba(250,252,255,.92), rgba(234,243,255,.82))",
    boxShadow: "0 4px 10px rgba(70,106,172,.07), inset 0 1px 0 #fff",
    textTransform: "none",
    fontSize: 14,
    fontWeight: 600,
    color: "#536A8A",
  },
  "& .MuiToggleButton-root.Mui-selected": {
    color: "#4E68C9",
    border: "1px solid rgba(125,150,212,.78)",
    background:
      "linear-gradient(145deg, rgba(233,237,255,.98), rgba(224,237,255,.94))",
    boxShadow:
      "0 5px 12px rgba(91,103,197,.13), inset 0 1px 0 rgba(255,255,255,.98), inset 0 -1px 0 rgba(125,150,212,.14)",
    "&:hover": {
      background:
        "linear-gradient(145deg, rgba(233,237,255,.98), rgba(224,237,255,.94))",
    },
  },
};

export const glassDialogSecondaryButtonSx = {
  minHeight: 44,
  px: 2,
  borderRadius: "14px",
  borderColor: "rgba(133,157,194,.5)",
  color: "#536A8A",
  background:
    "linear-gradient(145deg, rgba(255,255,255,.86), rgba(238,245,255,.76))",
  boxShadow: "0 3px 9px rgba(75,101,145,.08), inset 0 1px 0 #fff",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": {
    borderColor: "rgba(116,150,208,.72)",
    background:
      "linear-gradient(145deg, rgba(240,247,255,.98), rgba(228,239,255,.94))",
    boxShadow: "0 5px 11px rgba(75,96,151,.1), inset 0 1px 0 #fff",
  },
};

export const glassDialogDangerButtonSx = {
  minHeight: 44,
  px: 2,
  borderRadius: "14px",
  color: "#fff",
  background:
    "linear-gradient(115deg, #E66A80 0%, #D94F68 100%)",
  boxShadow:
    "0 7px 16px rgba(176,54,79,.2), inset 0 1px 0 rgba(255,255,255,.35)",
  textTransform: "none",
  fontWeight: 600,
  "&:hover": {
    background: "linear-gradient(115deg, #DB5B73 0%, #CA3F59 100%)",
    boxShadow:
      "0 9px 18px rgba(176,54,79,.25), inset 0 1px 0 rgba(255,255,255,.38)",
  },
  "&.Mui-disabled": {
    color: "rgba(255,255,255,.82)",
    background: "linear-gradient(115deg, #D99BA6, #D38897)",
  },
};
