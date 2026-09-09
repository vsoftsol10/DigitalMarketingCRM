// import {
//   FormControlLabel,
//   Stack,
//   Switch,
// } from "@mui/material";

// import { Controller, useFormContext } from "react-hook-form";

// export default function AIContentOptions() {
//   const { control } = useFormContext();

//   return (
//     <Stack spacing={1}>
//       <Controller
//         name="ai_include_emoji"
//         control={control}
//         render={({ field }) => (
//           <FormControlLabel
//             control={
//               <Switch
//                 checked={field.value}
//                 onChange={(e) =>
//                   field.onChange(e.target.checked)
//                 }
//               />
//             }
//             label="Include Emojis"
//           />
//         )}
//       />

//       <Controller
//         name="ai_include_hashtags"
//         control={control}
//         render={({ field }) => (
//           <FormControlLabel
//             control={
//               <Switch
//                 checked={field.value}
//                 onChange={(e) =>
//                   field.onChange(e.target.checked)
//                 }
//               />
//             }
//             label="Include Hashtags"
//           />
//         )}
//       />

//       <Controller
//         name="ai_include_cta"
//         control={control}
//         render={({ field }) => (
//           <FormControlLabel
//             control={
//               <Switch
//                 checked={field.value}
//                 onChange={(e) =>
//                   field.onChange(e.target.checked)
//                 }
//               />
//             }
//             label="Include Call To Action"
//           />
//         )}
//       />
//     </Stack>
//   );
// }
import {
  Box,
  FormControlLabel,
  Stack,
  Switch,
  Typography,
} from "@mui/material";

import { Controller, useFormContext } from "react-hook-form";

export default function AIContentOptions() {
  const { control } = useFormContext();

  return (
    <Box
      sx={{
        px: 1.5,
        py: 1,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
        bgcolor: "background.paper",
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        spacing={{
          xs: 1.5,
          sm: 3,
        }}
        flexWrap="wrap"
        useFlexGap
      >
        <Typography
          sx={{
            fontSize: 13,
            fontWeight: 600,
            color: "text.secondary",
            mr: 0.5,
          }}
        >
          Include
        </Typography>

        <Controller
          name="ai_include_emoji"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              sx={{
                m: 0,
              }}
              control={
                <Switch
                  size="small"
                  checked={Boolean(field.value)}
                  onChange={(event) =>
                    field.onChange(event.target.checked)
                  }
                />
              }
              label={
                <Typography sx={{ fontSize: 13 }}>
                  Emojis
                </Typography>
              }
            />
          )}
        />

        <Controller
          name="ai_include_hashtags"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              sx={{
                m: 0,
              }}
              control={
                <Switch
                  size="small"
                  checked={Boolean(field.value)}
                  onChange={(event) =>
                    field.onChange(event.target.checked)
                  }
                />
              }
              label={
                <Typography sx={{ fontSize: 13 }}>
                  Hashtags
                </Typography>
              }
            />
          )}
        />

        <Controller
          name="ai_include_cta"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              sx={{
                m: 0,
              }}
              control={
                <Switch
                  size="small"
                  checked={Boolean(field.value)}
                  onChange={(event) =>
                    field.onChange(event.target.checked)
                  }
                />
              }
              label={
                <Typography sx={{ fontSize: 13 }}>
                  Call to action
                </Typography>
              }
            />
          )}
        />
      </Stack>
    </Box>
  );
}