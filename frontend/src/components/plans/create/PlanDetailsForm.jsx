// import { Box, Grid, TextField, Typography } from "@mui/material";

// import KeyboardArrowDownRoundedIcon from "@mui/icons-material/KeyboardArrowDownRounded";

// import { Controller, useFormContext } from "react-hook-form";

// import { PLAN_TYPES } from "../../../constants/plan.constants";

// const FIELD_HEIGHT = 52;

// const fieldLabelSx = {
//   display: "block",

//   fontSize: "14px",
//   fontWeight: 500,
//   lineHeight: "20px",

//   color: "#475569",

//   mb: 0.75,
// };

// const inputSx = {
//   width: "100%",

//   "& .MuiOutlinedInput-root": {
//     height: FIELD_HEIGHT,
//     minHeight: FIELD_HEIGHT,

//     boxSizing: "border-box",

//     borderRadius: "14px",

//     backgroundColor: "#FFFFFF",

//     "& fieldset": {
//       borderColor: "#CBD5E1",
//       borderWidth: "1px",
//     },

//     "&:hover fieldset": {
//       borderColor: "#CBD5E1",
//     },

//     "&.Mui-focused fieldset": {
//       borderColor: "#2563EB",
//       borderWidth: "1px",
//     },
//   },

//   "& .MuiOutlinedInput-input": {
//     height: FIELD_HEIGHT,
//     boxSizing: "border-box",

//     padding: "0 16px",

//     fontSize: "16px",
//     fontWeight: 400,
//     lineHeight: "20px",

//     color: "#334155",

//     "&::placeholder": {
//       color: "#94A3B8",
//       opacity: 1,
//     },
//   },

//   "& .MuiFormHelperText-root": {
//     marginLeft: 0,
//     marginTop: "4px",

//     fontSize: "12px",
//   },
// };

// /*
//  * Plan Type now uses the SAME pattern as
//  * every other field: FieldLabel above,
//  * plain bordered box below.
//  *
//  * This keeps it visually identical to
//  * Name / Description / Status instead of
//  * the old MUI "notched" floating-label look.
//  */
// const selectBoxSx = {
//   position: "relative",

//   width: "100%",
//   height: FIELD_HEIGHT,

//   boxSizing: "border-box",

//   border: "1px solid #CBD5E1",
//   borderRadius: "14px",

//   backgroundColor: "#FFFFFF",

//   display: "flex",
//   alignItems: "center",

//   transition: "border-color 150ms ease, box-shadow 150ms ease",

//   "&:hover": {
//     borderColor: "#94A3B8",
//   },

//   "&:focus-within": {
//     borderColor: "#2563EB",
//     boxShadow: "0 0 0 1px #2563EB",
//   },
// };

// const selectSx = {
//   width: "100%",
//   height: FIELD_HEIGHT,

//   minWidth: 0,

//   padding: "0 42px 0 16px",

//   border: 0,
//   outline: 0,

//   backgroundColor: "transparent",

//   color: "#334155",

//   fontFamily: "inherit",

//   fontSize: "16px",
//   fontWeight: 400,
//   lineHeight: "20px",

//   cursor: "pointer",

//   appearance: "none",
//   WebkitAppearance: "none",
//   MozAppearance: "none",

//   boxSizing: "border-box",
// };

// /*
//  * Status buttons — border color now matches
//  * the default #CBD5E1 used by every other
//  * field (was #E2E8F0 before, which is why it
//  * looked slightly "off").
//  */
// const statusButtonSx = {
//   width: "100%",
//   height: FIELD_HEIGHT,
//   minHeight: FIELD_HEIGHT,

//   borderRadius: "14px",

//   border: "1px solid #CBD5E1",

//   backgroundColor: "#FFFFFF",

//   color: "#64748B",

//   fontSize: "16px",
//   fontWeight: 400,
//   lineHeight: "20px",

//   textTransform: "none",

//   display: "flex",
//   alignItems: "center",
//   justifyContent: "center",

//   gap: 1,

//   padding: 0,

//   cursor: "pointer",

//   boxSizing: "border-box",

//   transition:
//     "border-color 150ms ease, background-color 150ms ease, color 150ms ease",

//   "&:hover": {
//     backgroundColor: "#F8FAFC",
//     borderColor: "#94A3B8",
//   },
// };

// function FieldLabel({ children, required = false }) {
//   return (
//     <Typography component="div" sx={fieldLabelSx}>
//       {children}

//       {required && (
//         <Box
//           component="span"
//           sx={{
//             color: "#EF4444",
//             ml: 0.25,
//           }}
//         >
//           *
//         </Box>
//       )}
//     </Typography>
//   );
// }

// export default function PlanDetailsForm() {
//   const {
//     control,
//     formState: { errors },
//   } = useFormContext();

//   return (
//     <Box
//       sx={{
//         width: "100%",
//       }}
//     >
//       {/* =========================
//           SECTION HEADER
//       ========================= */}

//       <Typography
//         component="h2"
//         sx={{
//           margin: 0,

//           fontSize: "20px",
//           fontWeight: 700,
//           lineHeight: "28px",

//           color: "#1E293B",
//         }}
//       >
//         Basic Plan Details
//       </Typography>

//       <Typography
//         component="p"
//         sx={{
//           margin: 0,

//           mt: 0.5,
//           mb: 2.75,

//           fontSize: "16px",
//           fontWeight: 400,
//           lineHeight: "24px",

//           color: "#64748B",
//         }}
//       >
//         Name, description, type, and status.
//       </Typography>

//       {/* =========================
//           FORM
//       ========================= */}

//       <Grid container columnSpacing={2.5} rowSpacing={2.25}>
//         {/* =========================
//             PLAN NAME
//         ========================= */}

//         <Grid size={12}>
//           <FieldLabel required>Plan Name</FieldLabel>

//           <Controller
//             name="name"
//             control={control}
//             render={({ field }) => (
//               <TextField
//                 {...field}
//                 fullWidth
//                 placeholder="e.g. Basic"
//                 error={Boolean(errors.name)}
//                 helperText={errors.name?.message}
//                 sx={inputSx}
//               />
//             )}
//           />
//         </Grid>

//         {/* =========================
//             PLAN DESCRIPTION
//         ========================= */}

//         <Grid size={12}>
//           <FieldLabel required>Plan Description</FieldLabel>

//           <Controller
//             name="description"
//             control={control}
//             render={({ field }) => (
//               <TextField
//                 {...field}
//                 fullWidth
//                 placeholder="e.g. Perfect for startups and small businesses"
//                 error={Boolean(errors.description)}
//                 helperText={errors.description?.message}
//                 sx={inputSx}
//               />
//             )}
//           />
//         </Grid>

//         {/* =========================
//             PLAN TYPE
//             (now same pattern as Name/Description/Status)
//         ========================= */}

//         <Grid
//           size={{
//             xs: 12,
//             md: 6,
//           }}
//         >
//           <FieldLabel required>Plan Type</FieldLabel>

//           <Controller
//             name="type"
//             control={control}
//             render={({ field }) => (
//               <Box>
//                 <Box sx={selectBoxSx}>
//                   <Box
//                     component="select"
//                     {...field}
//                     value={field.value || ""}
//                     sx={selectSx}
//                   >
//                     {PLAN_TYPES.map((type) => (
//                       <option key={type} value={type}>
//                         {type}
//                       </option>
//                     ))}
//                   </Box>

//                   <KeyboardArrowDownRoundedIcon
//                     sx={{
//                       position: "absolute",

//                       right: 12,
//                       top: "50%",

//                       transform: "translateY(-50%)",

//                       fontSize: 22,

//                       color: "#64748B",

//                       pointerEvents: "none",
//                     }}
//                   />
//                 </Box>

//                 {errors.type && (
//                   <Typography
//                     sx={{
//                       mt: 0.5,

//                       fontSize: "12px",
//                       lineHeight: "16px",

//                       color: "#EF4444",
//                     }}
//                   >
//                     {errors.type.message}
//                   </Typography>
//                 )}
//               </Box>
//             )}
//           />
//         </Grid>

//         {/* =========================
//             STATUS
//         ========================= */}

//         <Grid
//           size={{
//             xs: 12,
//             md: 6,
//           }}
//         >
//           <FieldLabel required>Status</FieldLabel>

//           <Controller
//             name="status"
//             control={control}
//             render={({ field }) => {
//               const isActive = field.value === "active";

//               const isInactive = field.value === "inactive";

//               return (
//                 <Box
//                   sx={{
//                     width: "100%",

//                     height: FIELD_HEIGHT,

//                     display: "grid",

//                     gridTemplateColumns: "1fr 1fr",

//                     gap: 1,
//                   }}
//                 >
//                   {/* ACTIVE */}

//                   <Box
//                     component="button"
//                     type="button"
//                     onClick={() => field.onChange("active")}
//                     sx={{
//                       ...statusButtonSx,

//                       ...(isActive && {
//                         borderColor: "#2563EB",

//                         backgroundColor: "#EFF6FF",

//                         color: "#2563EB",

//                         "&:hover": {
//                           backgroundColor: "#EFF6FF",

//                           borderColor: "#2563EB",
//                         },
//                       }),
//                     }}
//                   >
//                     <Box
//                       sx={{
//                         width: 9,
//                         height: 9,

//                         flexShrink: 0,

//                         borderRadius: "50%",

//                         backgroundColor: "#16A34A",
//                       }}
//                     />
//                     Active
//                   </Box>

//                   {/* INACTIVE */}

//                   <Box
//                     component="button"
//                     type="button"
//                     onClick={() => field.onChange("inactive")}
//                     sx={{
//                       ...statusButtonSx,

//                       ...(isInactive && {
//                         borderColor: "#2563EB",

//                         backgroundColor: "#EFF6FF",

//                         color: "#2563EB",

//                         "&:hover": {
//                           backgroundColor: "#EFF6FF",

//                           borderColor: "#2563EB",
//                         },
//                       }),
//                     }}
//                   >
//                     <Box
//                       sx={{
//                         width: 9,
//                         height: 9,

//                         flexShrink: 0,

//                         borderRadius: "50%",

//                         backgroundColor: "#94A3B8",
//                       }}
//                     />
//                     Inactive
//                   </Box>
//                 </Box>
//               );
//             }}
//           />

//           {errors.status && (
//             <Typography
//               sx={{
//                 mt: 0.5,

//                 fontSize: "12px",
//                 lineHeight: "16px",

//                 color: "#EF4444",
//               }}
//             >
//               {errors.status.message}
//             </Typography>
//           )}
//         </Grid>
//       </Grid>
//     </Box>
//   );
// }

import { Box, Grid, TextField, Typography } from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";
import { useEffect } from "react";

const FIELD_HEIGHT = 52;

// ============================================================
// COMMON FIELD STYLES
// ============================================================

const fieldLabelSx = {
  display: "block",

  fontSize: "14px",
  fontWeight: 500,
  lineHeight: "20px",

  color: "#475569",

  mb: 0.75,
};

const inputSx = {
  width: "100%",

  "& .MuiOutlinedInput-root": {
    height: FIELD_HEIGHT,
    minHeight: FIELD_HEIGHT,

    boxSizing: "border-box",

    borderRadius: "14px",

    backgroundColor: "#FFFFFF",

    "& fieldset": {
      borderColor: "#CBD5E1",
      borderWidth: "1px",
    },

    "&:hover fieldset": {
      borderColor: "#CBD5E1",
    },

    "&.Mui-focused fieldset": {
      borderColor: "#2563EB",
      borderWidth: "1px",
    },

    "&.Mui-disabled": {
      backgroundColor: "#F8FAFC",
    },

    "&.Mui-disabled fieldset": {
      borderColor: "#CBD5E1",
    },
  },

  "& .MuiOutlinedInput-input": {
    height: FIELD_HEIGHT,
    boxSizing: "border-box",

    padding: "0 16px",

    fontSize: "16px",
    fontWeight: 400,
    lineHeight: "20px",

    color: "#334155",

    "&::placeholder": {
      color: "#94A3B8",
      opacity: 1,
    },

    "&.Mui-disabled": {
      WebkitTextFillColor: "#64748B",
    },
  },

  "& .MuiFormHelperText-root": {
    marginLeft: 0,
    marginTop: "4px",

    fontSize: "12px",
  },
};

// ============================================================
// FIELD LABEL
// ============================================================

function FieldLabel({ children, required = false }) {
  return (
    <Typography component="div" sx={fieldLabelSx}>
      {children}

      {required && (
        <Box
          component="span"
          sx={{
            color: "#EF4444",
            ml: 0.25,
          }}
        >
          *
        </Box>
      )}
    </Typography>
  );
}

// ============================================================
// STATUS BUTTON STYLES
// ============================================================

const statusButtonSx = {
  width: "100%",
  height: FIELD_HEIGHT,
  minHeight: FIELD_HEIGHT,

  borderRadius: "14px",

  border: "1px solid #CBD5E1",

  backgroundColor: "#FFFFFF",

  color: "#64748B",

  fontSize: "16px",
  fontWeight: 400,
  lineHeight: "20px",

  textTransform: "none",

  display: "flex",
  alignItems: "center",
  justifyContent: "center",

  gap: 1,

  padding: 0,

  cursor: "pointer",

  boxSizing: "border-box",

  transition:
    "border-color 150ms ease, background-color 150ms ease, color 150ms ease",

  "&:hover": {
    backgroundColor: "#F8FAFC",
    borderColor: "#94A3B8",
  },
};

// ============================================================
// PLAN DETAILS FORM
// ============================================================

export default function PlanDetailsForm({ customPlan = false }) {
  const {
    control,
    watch,
    setValue,
    formState: { errors },
  } = useFormContext();

  const planName = watch("name");

  // ==========================================================
  // PLAN TYPE SYNC
  // ==========================================================

  useEffect(() => {
    // --------------------------------------------------------
    // Custom Plan
    // --------------------------------------------------------

    if (customPlan) {
      if (planName?.trim()) {
        setValue("type", "Custom", {
          shouldValidate: true,
          shouldDirty: false,
        });
      } else {
        setValue("type", "Custom", {
          shouldValidate: false,
          shouldDirty: false,
        });
      }

      return;
    }

    // --------------------------------------------------------
    // Normal Plan
    // --------------------------------------------------------

    const normalizedName = planName?.trim() || "";

    setValue("type", normalizedName, {
      shouldValidate: Boolean(normalizedName),
      shouldDirty: false,
    });
  }, [customPlan, planName, setValue]);

  return (
    <Box
      sx={{
        width: "100%",
      }}
    >
      {/* =====================================================
          SECTION HEADER
      ===================================================== */}

      <Typography
        component="h2"
        sx={{
          margin: 0,

          fontSize: "20px",
          fontWeight: 700,
          lineHeight: "28px",

          color: "#1E293B",
        }}
      >
        Basic Plan Details
      </Typography>

      <Typography
        component="p"
        sx={{
          margin: 0,

          mt: 0.5,
          mb: 2.75,

          fontSize: "16px",
          fontWeight: 400,
          lineHeight: "24px",

          color: "#64748B",
        }}
      >
        Name, description, type, and status.
      </Typography>

      {/* =====================================================
          FORM
      ===================================================== */}

      <Grid container columnSpacing={2.5} rowSpacing={2.25}>
        {/* ===================================================
            PLAN NAME
        =================================================== */}

        <Grid size={12}>
          <FieldLabel required>Plan Name</FieldLabel>

          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                placeholder="e.g. Professional"
                error={Boolean(errors.name)}
                helperText={errors.name?.message}
                sx={inputSx}
              />
            )}
          />
        </Grid>

        {/* ===================================================
            PLAN DESCRIPTION
        =================================================== */}

        <Grid size={12}>
          <FieldLabel required>Plan Description</FieldLabel>

          <Controller
            name="description"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                placeholder="e.g. Perfect for growing businesses"
                error={Boolean(errors.description)}
                helperText={errors.description?.message}
                sx={inputSx}
              />
            )}
          />
        </Grid>

        {/* ===================================================
            PLAN TYPE
        =================================================== */}

        <Grid
          size={{
            xs: 12,
            md: 6,
          }}
        >
          <FieldLabel required>Plan Type</FieldLabel>

          <Controller
            name="type"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                value={field.value || ""}
                disabled={customPlan}
                placeholder={
                  customPlan
                    ? "Custom"
                    : "Automatically generated from plan name"
                }
                error={Boolean(errors.type)}
                helperText={
                  errors.type?.message ||
                  (customPlan
                    ? "Custom plan type is fixed."
                    : "Automatically generated from the plan name.")
                }
                sx={inputSx}
              />
            )}
          />
        </Grid>

        {/* ===================================================
            STATUS
        =================================================== */}

        <Grid
          size={{
            xs: 12,
            md: 6,
          }}
        >
          <FieldLabel required>Status</FieldLabel>

          <Controller
            name="status"
            control={control}
            render={({ field }) => {
              const isActive = field.value === "active";

              const isInactive = field.value === "inactive";

              return (
                <Box
                  sx={{
                    width: "100%",

                    height: FIELD_HEIGHT,

                    display: "grid",

                    gridTemplateColumns: "1fr 1fr",

                    gap: 1,
                  }}
                >
                  {/* ACTIVE */}

                  <Box
                    component="button"
                    type="button"
                    onClick={() => field.onChange("active")}
                    sx={{
                      ...statusButtonSx,

                      ...(isActive && {
                        borderColor: "#2563EB",

                        backgroundColor: "#EFF6FF",

                        color: "#2563EB",

                        "&:hover": {
                          backgroundColor: "#EFF6FF",

                          borderColor: "#2563EB",
                        },
                      }),
                    }}
                  >
                    <Box
                      sx={{
                        width: 9,
                        height: 9,

                        flexShrink: 0,

                        borderRadius: "50%",

                        backgroundColor: "#16A34A",
                      }}
                    />
                    Active
                  </Box>

                  {/* INACTIVE */}

                  <Box
                    component="button"
                    type="button"
                    onClick={() => field.onChange("inactive")}
                    sx={{
                      ...statusButtonSx,

                      ...(isInactive && {
                        borderColor: "#2563EB",

                        backgroundColor: "#EFF6FF",

                        color: "#2563EB",

                        "&:hover": {
                          backgroundColor: "#EFF6FF",

                          borderColor: "#2563EB",
                        },
                      }),
                    }}
                  >
                    <Box
                      sx={{
                        width: 9,
                        height: 9,

                        flexShrink: 0,

                        borderRadius: "50%",

                        backgroundColor: "#94A3B8",
                      }}
                    />
                    Inactive
                  </Box>
                </Box>
              );
            }}
          />

          {errors.status && (
            <Typography
              sx={{
                mt: 0.5,

                fontSize: "12px",
                lineHeight: "16px",

                color: "#EF4444",
              }}
            >
              {errors.status.message}
            </Typography>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
