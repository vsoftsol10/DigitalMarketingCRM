// import {
//   Box,
//   Grid,
//   TextField,
//   ToggleButton,
//   ToggleButtonGroup,
//   Typography,
// } from "@mui/material";

// import { Controller, useFormContext } from "react-hook-form";

// import { TYPOGRAPHY } from "../../../theme/typography";

// const FIELD_HEIGHT = 52;

// // Same tokens as PlanDetailsForm / PlanLimitsForm — keep in sync
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

//     padding: "0 16px 0 8px",

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

// // Height + border now match FIELD_HEIGHT (52) and #CBD5E1 like every other field
// const cycleSx = {
//   flex: 1,

//   height: FIELD_HEIGHT,

//   borderRadius: "14px !important",

//   border: "1px solid #CBD5E1 !important",

//   textTransform: "none",

//   fontSize: "16px",
//   fontWeight: 400,

//   color: "#64748B",

//   "&.Mui-selected": {
//     bgcolor: "#EFF6FF",
//     color: "#2563EB",
//     borderColor: "#2563EB !important",
//   },

//   "&.Mui-selected:hover": {
//     bgcolor: "#EFF6FF",
//   },

//   "&:hover": {
//     borderColor: "#94A3B8 !important",
//   },
// };

// export default function PricingForm() {
//   const {
//     control,
//     formState: { errors },
//   } = useFormContext();

//   return (
//     <Box>
//       <Typography sx={TYPOGRAPHY.sectionTitle}>Pricing</Typography>

//       <Typography
//         sx={{
//           ...TYPOGRAPHY.sectionDescription,
//           mt: 0.25,
//           mb: 2.75,
//         }}
//       >
//         Set monthly and yearly pricing for this plan.
//       </Typography>

//       <FieldLabel required>Billing Cycle</FieldLabel>

//       <Controller
//         name="billing_cycle"
//         control={control}
//         render={({ field }) => (
//           <ToggleButtonGroup
//             exclusive
//             fullWidth
//             value={field.value}
//             onChange={(_, value) => {
//               if (value) {
//                 field.onChange(value);
//               }
//             }}
//             sx={{
//               mb: 2.75,
//               gap: 1,
//             }}
//           >
//             <ToggleButton value="monthly" sx={cycleSx}>
//               Monthly
//             </ToggleButton>

//             <ToggleButton value="yearly" sx={cycleSx}>
//               Yearly
//             </ToggleButton>
//           </ToggleButtonGroup>
//         )}
//       />

//       <Grid container columnSpacing={2.5} rowSpacing={2.25}>
//         <Grid
//           size={{
//             xs: 12,
//             md: 6,
//           }}
//         >
//           <FieldLabel required>Monthly Price</FieldLabel>

//           <Controller
//             name="monthly_price"
//             control={control}
//             render={({ field }) => (
//               <TextField
//                 {...field}
//                 fullWidth
//                 type="number"
//                 placeholder="0"
//                 error={!!errors.monthly_price}
//                 helperText={
//                   errors.monthly_price?.message || "Price per month in INR"
//                 }
//                 sx={inputSx}
//                 slotProps={{
//                   input: {
//                     startAdornment: (
//                       <Box
//                         component="span"
//                         sx={{
//                           mr: 1,
//                           color: "#64748B",
//                         }}
//                       >
//                         ₹
//                       </Box>
//                     ),
//                   },
//                 }}
//               />
//             )}
//           />
//         </Grid>

//         <Grid
//           size={{
//             xs: 12,
//             md: 6,
//           }}
//         >
//           <FieldLabel required>Yearly Price</FieldLabel>

//           <Controller
//             name="yearly_price"
//             control={control}
//             render={({ field }) => (
//               <TextField
//                 {...field}
//                 fullWidth
//                 type="number"
//                 placeholder="0"
//                 error={!!errors.yearly_price}
//                 helperText={
//                   errors.yearly_price?.message || "Price per year in INR"
//                 }
//                 sx={inputSx}
//                 slotProps={{
//                   input: {
//                     startAdornment: (
//                       <Box
//                         component="span"
//                         sx={{
//                           mr: 1,
//                           color: "#64748B",
//                         }}
//                       >
//                         ₹
//                       </Box>
//                     ),
//                   },
//                 }}
//               />
//             )}
//           />
//         </Grid>
//       </Grid>
//     </Box>
//   );
// }

import { Box, Grid, TextField, Typography } from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";

const FIELD_HEIGHT = 52;

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
  },

  "& .MuiOutlinedInput-input": {
    height: FIELD_HEIGHT,
    boxSizing: "border-box",

    padding: "0 16px 0 8px",

    fontSize: "16px",
    fontWeight: 400,
    lineHeight: "20px",

    color: "#334155",

    "&::placeholder": {
      color: "#94A3B8",
      opacity: 1,
    },
  },

  "& .MuiFormHelperText-root": {
    marginLeft: 0,
    marginTop: "4px",

    fontSize: "12px",
  },
};

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

export default function PricingForm() {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  return (
    <Box>
      <Typography
        sx={{
          fontSize: "20px",
          fontWeight: 700,
          lineHeight: "28px",
          color: "#1E293B",
        }}
      >
        Pricing
      </Typography>

      <Typography
        sx={{
          mt: 0.25,
          mb: 2.75,

          fontSize: "16px",
          fontWeight: 400,
          lineHeight: "24px",

          color: "#64748B",
        }}
      >
        Set monthly and yearly pricing for this plan.
      </Typography>

      <Grid container columnSpacing={2.5} rowSpacing={2.25}>
        {/* =====================================================
            MONTHLY PRICE
        ===================================================== */}

        <Grid
          size={{
            xs: 12,
            md: 6,
          }}
        >
          <FieldLabel required>Monthly Price</FieldLabel>

          <Controller
            name="monthly_price"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                type="number"
                placeholder="0"
                error={Boolean(errors.monthly_price)}
                helperText={
                  errors.monthly_price?.message || "Price per month in INR"
                }
                sx={inputSx}
                slotProps={{
                  input: {
                    startAdornment: (
                      <Box
                        component="span"
                        sx={{
                          mr: 1,
                          color: "#64748B",
                        }}
                      >
                        ₹
                      </Box>
                    ),
                  },
                }}
              />
            )}
          />
        </Grid>

        {/* =====================================================
            YEARLY PRICE
        ===================================================== */}

        <Grid
          size={{
            xs: 12,
            md: 6,
          }}
        >
          <FieldLabel required>Yearly Price</FieldLabel>

          <Controller
            name="yearly_price"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                type="number"
                placeholder="0"
                error={Boolean(errors.yearly_price)}
                helperText={
                  errors.yearly_price?.message || "Price per year in INR"
                }
                sx={inputSx}
                slotProps={{
                  input: {
                    startAdornment: (
                      <Box
                        component="span"
                        sx={{
                          mr: 1,
                          color: "#64748B",
                        }}
                      >
                        ₹
                      </Box>
                    ),
                  },
                }}
              />
            )}
          />
        </Grid>
      </Grid>
    </Box>
  );
}
