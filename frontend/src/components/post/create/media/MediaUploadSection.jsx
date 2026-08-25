// // import SectionCard from "../SectionCard";

// // import MediaDropzone from "./MediaDropzone";
// // import MediaPreviewGrid from "./MediaPreviewGrid";

// // import useMediaUpload from "../../../../hooks/post/useMediaUpload";

// // export default function MediaUploadSection({
// //   config,
// // }) {
// //   const {
// //     media,

// //     inputRef,

// //     handleBrowse,

// //     handleInputChange,

// //     handleDrop,

// //     handleDragOver,

// //     removeMedia,
// //   } = useMediaUpload({
// //     config,
// //   });

// //   return (
// //     <SectionCard
// //       title="Media"
// //       description="Upload images or videos for your post."
// //     >
// //       <MediaDropzone
// //         config={config}
// //         inputRef={inputRef}
// //         onBrowse={handleBrowse}
// //         onInputChange={handleInputChange}
// //         onDrop={handleDrop}
// //         onDragOver={handleDragOver}
// //       />

// //       <MediaPreviewGrid
// //         media={media}
// //         onRemove={removeMedia}
// //       />
// //     </SectionCard>
// //   );
// // }

// import { Stack } from "@mui/material";

// import SectionCard from "../SectionCard";

// import MediaDropzone from "./MediaDropzone";
// import MediaPreviewGrid from "./MediaPreviewGrid";

// import useMediaUpload from "../../../../hooks/post/useMediaUpload";

// export default function MediaUploadSection({
//   config,
// }) {
//   const {
//     media,

//     inputRef,

//     handleBrowse,

//     handleInputChange,

//     handleDrop,

//     handleDragOver,

//     removeMedia,
//   } = useMediaUpload({
//     config,
//   });

//   return (
//     <SectionCard
//       title="Media"
//       description="Upload images or videos for your post."
//     >
//       <Stack spacing={3}>
//         <MediaDropzone
//           config={config}
//           inputRef={inputRef}
//           onBrowse={handleBrowse}
//           onInputChange={
//             handleInputChange
//           }
//           onDrop={handleDrop}
//           onDragOver={
//             handleDragOver
//           }
//         />

//         <MediaPreviewGrid
//           media={media}
//           onRemove={removeMedia}
//         />
//       </Stack>
//     </SectionCard>
//   );
// }

import {
  Stack,
  Typography,
} from "@mui/material";

import {
  useFormContext,
} from "react-hook-form";

import SectionCard from "../SectionCard";

import MediaDropzone from "./MediaDropzone";
import MediaPreviewGrid from "./MediaPreviewGrid";

import useMediaUpload from "../../../../hooks/post/useMediaUpload";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function MediaUploadSection({
  config,
}) {
  const {
    formState: { errors },
  } = useFormContext();

  const {
    media,

    inputRef,

    handleBrowse,

    handleInputChange,

    handleDrop,

    handleDragOver,

    removeMedia,
  } = useMediaUpload({
    config,
  });

  return (
    <SectionCard
      title="Media"
      description="Upload images or videos for your post."
    >
      <Stack spacing={3}>
        <MediaDropzone
          config={config}
          inputRef={inputRef}
          onBrowse={handleBrowse}
          onInputChange={
            handleInputChange
          }
          onDrop={handleDrop}
          onDragOver={
            handleDragOver
          }
        />

        {errors.media && (
          <Typography
            sx={{
              ...TYPOGRAPHY.helperText,
              color:
                "error.main",
              mt: -1,
            }}
          >
            {errors.media.message}
          </Typography>
        )}

        <MediaPreviewGrid
          media={media}
          onRemove={removeMedia}
        />
      </Stack>
    </SectionCard>
  );
}