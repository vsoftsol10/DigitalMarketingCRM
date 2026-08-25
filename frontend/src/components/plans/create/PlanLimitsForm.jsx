// import { Box, Grid, TextField, Typography } from "@mui/material";

// import { Controller, useFormContext } from "react-hook-form";

// import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
// import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
// import VideoLibraryOutlinedIcon from "@mui/icons-material/VideoLibraryOutlined";
// import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
// import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
// import StorageOutlinedIcon from "@mui/icons-material/StorageOutlined";

// import { TYPOGRAPHY } from "../../../theme/typography";

// const FIELD_HEIGHT = 52;

// // Same tokens as PlanDetailsForm — keep both files in sync if you change one
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

// const fields = [
//   {
//     name: "limits.accounts",
//     label: "Social Accounts",
//     icon: ShareOutlinedIcon,
//   },
//   {
//     name: "limits.posts",
//     label: "Posts / Posters (per month)",
//     icon: EditOutlinedIcon,
//   },
//   {
//     name: "limits.videos",
//     label: "Videos (per month)",
//     icon: VideoLibraryOutlinedIcon,
//   },
//   {
//     name: "limits.ads",
//     label: "Ads / Campaigns",
//     icon: CampaignOutlinedIcon,
//   },
//   {
//     name: "limits.dm_automations",
//     label: "DM Automations",
//     icon: AutoAwesomeOutlinedIcon,
//   },
//   {
//     name: "limits.storage_gb",
//     label: "Storage (GB)",
//     icon: StorageOutlinedIcon,
//   },
// ];

// export default function PlanLimitsForm() {
//   const {
//     control,
//     formState: { errors },
//   } = useFormContext();

//   return (
//     <Box>
//       <Typography sx={TYPOGRAPHY.sectionTitle}>Plan Limits</Typography>

//       <Typography
//         sx={{
//           ...TYPOGRAPHY.sectionDescription,
//           mt: 0.25,
//           mb: 2.75,
//         }}
//       >
//         Configure resource limits for organizations on this plan.
//       </Typography>

//       <Grid container columnSpacing={2.5} rowSpacing={2.25}>
//         {fields.map(({ name, label, icon: Icon }) => {
//           const error = name
//             .split(".")
//             .reduce((acc, key) => acc?.[key], errors);

//           return (
//             <Grid
//               key={name}
//               size={{
//                 xs: 12,
//                 md: 6,
//               }}
//             >
//               <FieldLabel required>{label}</FieldLabel>

//               <Controller
//                 name={name}
//                 control={control}
//                 render={({ field }) => (
//                   <TextField
//                     {...field}
//                     fullWidth
//                     type="number"
//                     placeholder="0"
//                     error={!!error}
//                     helperText={error?.message}
//                     sx={inputSx}
//                     slotProps={{
//                       input: {
//                         startAdornment: (
//                           <Icon
//                             sx={{
//                               mr: 1,
//                               fontSize: 19,
//                               color: "#64748B",
//                             }}
//                           />
//                         ),
//                       },
//                     }}
//                   />
//                 )}
//               />
//             </Grid>
//           );
//         })}
//       </Grid>
//     </Box>
//   );
// }

import {
  Box,
  Grid,
  TextField,
  Typography,
} from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";

import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import VideoLibraryOutlinedIcon from "@mui/icons-material/VideoLibraryOutlined";
import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";

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

function FieldLabel({
  children,
  required = false,
}) {
  return (
    <Typography
      component="div"
      sx={fieldLabelSx}
    >
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

const fields = [
  {
    name: "limits.accounts",
    label: "Social Accounts",
    icon: ShareOutlinedIcon,
  },
  {
    name: "limits.posts",
    label: "Posts / Posters (per month)",
    icon: EditOutlinedIcon,
  },
  {
    name: "limits.videos",
    label: "Videos (per month)",
    icon: VideoLibraryOutlinedIcon,
  },
  {
    name: "limits.ads",
    label: "Ads / Campaigns",
    icon: CampaignOutlinedIcon,
  },
  {
    name: "limits.dm_automations",
    label: "DM Automations",
    icon: AutoAwesomeOutlinedIcon,
  },
];

export default function PlanLimitsForm() {
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
        Plan Limits
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
        Configure resource limits for organizations
        on this plan.
      </Typography>

      <Grid
        container
        columnSpacing={2.5}
        rowSpacing={2.25}
      >
        {fields.map(
          ({
            name,
            label,
            icon: Icon,
          }) => {
            const error = name
              .split(".")
              .reduce(
                (acc, key) =>
                  acc?.[key],
                errors,
              );

            return (
              <Grid
                key={name}
                size={{
                  xs: 12,
                  md: 6,
                }}
              >
                <FieldLabel required>
                  {label}
                </FieldLabel>

                <Controller
                  name={name}
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      type="number"
                      placeholder="0"
                      error={Boolean(error)}
                      helperText={
                        error?.message
                      }
                      sx={inputSx}
                      slotProps={{
                        input: {
                          startAdornment: (
                            <Icon
                              sx={{
                                mr: 1,
                                fontSize: 19,
                                color:
                                  "#64748B",
                              }}
                            />
                          ),
                        },
                      }}
                    />
                  )}
                />
              </Grid>
            );
          },
        )}
      </Grid>
    </Box>
  );
}