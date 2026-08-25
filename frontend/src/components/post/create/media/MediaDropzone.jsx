// import {
//   Box,
//   Stack,
//   Typography,
// } from "@mui/material";

// import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";

// import SecondaryButton from "../../../ui/button/SecondaryButton";
// import { TYPOGRAPHY } from "../../../../theme/typography";

// export default function MediaDropzone({
//   config,
//   inputRef,
//   onBrowse,
//   onInputChange,
//   onDrop,
//   onDragOver,
// }) {
//   return (
//     <Box
//       onDrop={onDrop}
//       onDragOver={onDragOver}
//       sx={{
//         border: "2px dashed #CBD5E1",
//         borderRadius: "20px",
//         bgcolor: "#F8FAFC",
//         py: 6,
//         px: 4,
//         textAlign: "center",
//         transition: "all .2s",

//         "&:hover": {
//           borderColor: "#2563EB",
//           bgcolor: "#EFF6FF",
//         },
//       }}
//     >
//       <Stack spacing={2} alignItems="center">
//         <CloudUploadOutlinedIcon
//           sx={{
//             fontSize: 54,
//             color: "#2563EB",
//           }}
//         />

//         <Typography sx={TYPOGRAPHY.sectionTitle}>
//           Drag & Drop Media
//         </Typography>

//         <Typography sx={TYPOGRAPHY.bodySmall}>
//           Upload images or videos for your post
//         </Typography>

//         <SecondaryButton
//           fullWidth={false}
//           onClick={onBrowse}
//         >
//           Browse Files
//         </SecondaryButton>

//         <Typography sx={TYPOGRAPHY.caption}>
//           {config.accepted_extensions.join(" • ")}
//         </Typography>

//         <Typography sx={TYPOGRAPHY.caption}>
//           Maximum {config.max_files} files •{" "}
//           {config.max_file_size_mb} MB each
//         </Typography>
//       </Stack>

//       <input
//         hidden
//         multiple={config.allow_multiple}
//         ref={inputRef}
//         type="file"
//         accept={config.accepted_types.join(",")}
//         onChange={onInputChange}
//       />
//     </Box>
//   );
// }

import {
  Box,
  Stack,
  Typography,
} from "@mui/material";

import {
  useTheme,
} from "@mui/material/styles";

import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";

import SecondaryButton from "../../../ui/button/SecondaryButton";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function MediaDropzone({
  config,
  inputRef,
  onBrowse,
  onInputChange,
  onDrop,
  onDragOver,
}) {
  const theme = useTheme();

  return (
    <Box
      onDrop={onDrop}
      onDragOver={onDragOver}
      sx={{
        border: "2px dashed",
        borderColor:
          theme.palette.divider,

        borderRadius: 2.5,

        bgcolor:
          theme.palette.background
            .default,

        py: 6,
        px: 4,

        textAlign: "center",

        transition:
          "border-color 0.2s ease, background-color 0.2s ease",

        "&:hover": {
          borderColor:
            theme.palette.primary
              .main,

          bgcolor:
            theme.palette.action
              .hover,
        },
      }}
    >
      <Stack
        spacing={2}
        alignItems="center"
      >
        <CloudUploadOutlinedIcon
          sx={{
            fontSize: 54,
            color:
              theme.palette.primary
                .main,
          }}
        />

        <Typography
          sx={
            TYPOGRAPHY.sectionTitle
          }
        >
          Drag & Drop Media
        </Typography>

        <Typography
          sx={
            TYPOGRAPHY.bodySmall
          }
        >
          Upload images or videos
          for your post
        </Typography>

        <SecondaryButton
          fullWidth={false}
          onClick={onBrowse}
        >
          Browse Files
        </SecondaryButton>

        <Typography
          sx={
            TYPOGRAPHY.caption
          }
        >
          {config.accepted_extensions.join(
            " • ",
          )}
        </Typography>

        <Typography
          sx={
            TYPOGRAPHY.caption
          }
        >
          Maximum {config.max_files}{" "}
          files •{" "}
          {config.max_file_size_mb} MB
          each
        </Typography>
      </Stack>

      <input
        hidden
        multiple={
          config.allow_multiple
        }
        ref={inputRef}
        type="file"
        accept={config.accepted_types.join(
          ",",
        )}
        onChange={onInputChange}
      />
    </Box>
  );
}