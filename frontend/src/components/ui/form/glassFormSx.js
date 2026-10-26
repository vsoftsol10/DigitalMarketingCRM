export const glassFormPaperSx = {
  width: "100%",
  minWidth: 0,
  mx: "auto",
  p: { xs: 2, sm: 3, md: 4 },
  boxSizing: "border-box",
  borderRadius: "24px",
  border: "1px solid rgba(255,255,255,.96)",
  background:
    "radial-gradient(ellipse at 100% 0%, rgba(241,215,255,.32), transparent 34%), radial-gradient(ellipse at 0% 100%, rgba(211,231,255,.32), transparent 42%), linear-gradient(145deg, rgba(255,255,255,.98), rgba(238,245,255,.91) 48%, rgba(255,248,255,.88))",
  boxShadow:
    "0 20px 42px rgba(66,91,146,.14), 0 5px 14px rgba(91,109,161,.07), inset 0 2px 0 rgba(255,255,255,.99), inset 0 -2px 0 rgba(134,150,192,.10)",
  backdropFilter: "blur(18px)",
  "& .MuiOutlinedInput-root": {
    borderRadius: "15px",
    background:
      "linear-gradient(145deg, rgba(232,241,255,.82), rgba(255,255,255,.96) 58%, rgba(246,244,255,.9))",
    boxShadow:
      "inset 0 2px 5px rgba(77,102,145,.07), inset 0 1px 0 rgba(255,255,255,.96), 0 5px 12px rgba(79,102,153,.08)",
    transition: "border-color .18s ease, box-shadow .18s ease, background .18s ease",
    "& fieldset, & .MuiOutlinedInput-notchedOutline": {
      borderColor: "rgba(255,255,255,.98)",
      boxShadow: "0 0 0 1px rgba(142,164,204,.34)",
    },
    "&:hover fieldset, &:hover .MuiOutlinedInput-notchedOutline": {
      borderColor: "rgba(135,158,211,.78)",
    },
    "&.Mui-focused fieldset, &.Mui-focused .MuiOutlinedInput-notchedOutline": {
      borderColor: "#7D96D4",
      borderWidth: 1,
      boxShadow: "0 0 0 3px rgba(125,150,212,.13)",
    },
    "&.Mui-error .MuiOutlinedInput-notchedOutline": {
      borderColor: "rgba(220,38,38,.78)",
      boxShadow: "0 0 0 2px rgba(220,38,38,.08)",
    },
  },
  "& .MuiFormHelperText-root.Mui-error": {
    mt: 0.75,
    mx: 0,
    color: "#DC2626",
    fontSize: "13px",
    fontWeight: 500,
    lineHeight: 1.45,
    whiteSpace: "normal",
    overflowWrap: "anywhere",
  },
  "& .MuiFormControl-root.Mui-error > .MuiTypography-root": {
    mt: 0.75,
    color: "#DC2626",
    fontSize: "13px",
    fontWeight: 500,
    lineHeight: 1.45,
    whiteSpace: "normal",
    overflowWrap: "anywhere",
  },
};

export const glassFieldErrorInputSx = {
  "&.Mui-error .MuiOutlinedInput-notchedOutline": {
    borderColor: "#DC2626",
    borderWidth: 1,
    boxShadow: "0 0 0 2px rgba(220,38,38,.08)",
  },
};

export const glassFieldErrorMessageSx = {
  mt: 0.75,
  mx: 0,
  color: "#DC2626",
  fontSize: "13px",
  fontWeight: 500,
  lineHeight: 1.45,
  whiteSpace: "normal",
  overflowWrap: "anywhere",
};

export const glassPrimaryButtonSx = {
  borderRadius: "17px",
  border: "1px solid rgba(255,255,255,.7)",
  background: "linear-gradient(115deg, #A96BEA 0%, #7074ED 54%, #4A91ED 100%)",
  boxShadow:
    "0 11px 22px rgba(100,92,203,.3), 0 3px 7px rgba(65,101,210,.17), inset 0 1px 0 rgba(255,255,255,.46), inset 0 -2px 3px rgba(67,71,163,.16)",
  "&:hover": {
    background: "linear-gradient(115deg, #9D60E3 0%, #5E70E8 56%, #3D8FEA 100%)",
    boxShadow:
      "0 13px 24px rgba(100,92,203,.34), 0 3px 8px rgba(65,101,210,.2), inset 0 1px 0 rgba(255,255,255,.42)",
  },
  "&:focus-visible": {
    outline: "2px solid #7E8FE8",
    outlineOffset: 3,
  },
  "&.Mui-disabled": {
    color: "rgba(255,255,255,.78)",
    background: "linear-gradient(115deg, #B993DD, #929BE1)",
  },
};

export const glassFormSectionSx = {
  minWidth: 0,
  p: { xs: 2, sm: 2.5 },
  borderRadius: "20px",
  background:
    "radial-gradient(ellipse at 100% 0%, rgba(232,216,255,.24), transparent 34%), linear-gradient(145deg, rgba(239,246,255,.82), rgba(255,255,255,.76) 52%, rgba(249,243,255,.72))",
  border: "1px solid rgba(255,255,255,.96)",
  boxShadow:
    "0 10px 24px rgba(73,99,153,.10), 0 2px 5px rgba(99,117,167,.06), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -1px 0 rgba(121,145,189,.10)",
  backdropFilter: "blur(14px)",
};

export const glassFormDividerSx = {
  my: { xs: 2.5, sm: 3.5 },
  borderColor: "rgba(146,168,201,.28)",
};
