// import {
//   Box,
//   IconButton,
//   Typography,
// } from "@mui/material";

// import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
// import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
// import VideocamOutlinedIcon from "@mui/icons-material/VideocamOutlined";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// export default function MediaPreviewItem({
//   media,
//   onRemove,
// }) {
//   return (
//     <Box
//       sx={{
//         position: "relative",
//         border: "1px solid #E2E8F0",
//         borderRadius: "16px",
//         overflow: "hidden",
//         bgcolor: "#FFFFFF",
//       }}
//     >
//       {/* Preview */}

//       <Box
//         sx={{
//           height: 180,
//           bgcolor: "#F8FAFC",
//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",
//         }}
//       >
//         {media.type === "IMAGE" ? (
//           <Box
//             component="img"
//             src={media.preview}
//             alt={media.name}
//             sx={{
//               width: "100%",
//               height: "100%",
//               objectFit: "cover",
//             }}
//           />
//         ) : (
//           <Box
//             sx={{
//               display: "flex",
//               flexDirection: "column",
//               alignItems: "center",
//               gap: 1,
//             }}
//           >
//             <VideocamOutlinedIcon
//               sx={{
//                 fontSize: 42,
//                 color: "#2563EB",
//               }}
//             />

//             <Typography sx={TYPOGRAPHY.bodySmall}>
//               Video Preview
//             </Typography>
//           </Box>
//         )}
//       </Box>

//       {/* Delete */}

//       <IconButton
//         onClick={() => onRemove(media.id)}
//         size="small"
//         sx={{
//           position: "absolute",
//           top: 8,
//           right: 8,
//           bgcolor: "#FFFFFF",

//           "&:hover": {
//             bgcolor: "#F8FAFC",
//           },
//         }}
//       >
//         <DeleteOutlineRoundedIcon
//           fontSize="small"
//         />
//       </IconButton>

//       {/* Footer */}

//       <Box
//         sx={{
//           p: 2,
//         }}
//       >
//         <Box
//           sx={{
//             display: "flex",
//             alignItems: "center",
//             gap: 1,
//           }}
//         >
//           {media.type === "IMAGE" ? (
//             <ImageOutlinedIcon
//               fontSize="small"
//             />
//           ) : (
//             <VideocamOutlinedIcon
//               fontSize="small"
//             />
//           )}

//           <Typography
//             noWrap
//             sx={TYPOGRAPHY.bodySmall}
//           >
//             {media.name}
//           </Typography>
//         </Box>
//       </Box>
//     </Box>
//   );
// }

import {
  Box,
  IconButton,
  Typography,
} from "@mui/material";

import {
  useTheme,
} from "@mui/material/styles";

import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import VideocamOutlinedIcon from "@mui/icons-material/VideocamOutlined";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function MediaPreviewItem({
  media,
  onRemove,
}) {
  const theme = useTheme();

  const isImage =
    media.type === "IMAGE";

  return (
    <Box
      sx={{
        position: "relative",

        border: "1px solid",
        borderColor:
          theme.palette.divider,

        borderRadius: 2,

        overflow: "hidden",

        bgcolor:
          theme.palette.background
            .paper,
      }}
    >
      {/* Preview */}

      <Box
        sx={{
          height: 180,

          bgcolor:
            theme.palette.background
              .default,

          display: "flex",

          alignItems: "center",

          justifyContent: "center",
        }}
      >
        {isImage ? (
          <Box
            component="img"
            src={media.preview}
            alt={media.name}
            sx={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              display: "block",
            }}
          />
        ) : (
          <Box
            sx={{
              display: "flex",
              flexDirection:
                "column",
              alignItems:
                "center",
              gap: 1,
            }}
          >
            <VideocamOutlinedIcon
              sx={{
                fontSize: 42,
                color:
                  theme.palette
                    .primary.main,
              }}
            />

            <Typography
              sx={
                TYPOGRAPHY.bodySmall
              }
            >
              Video Preview
            </Typography>
          </Box>
        )}
      </Box>

      {/* Remove */}

      <IconButton
        aria-label={`Remove ${media.name}`}
        onClick={() =>
          onRemove(media.id)
        }
        size="small"
        sx={{
          position: "absolute",

          top: 8,
          right: 8,

          bgcolor:
            theme.palette
              .background.paper,

          border: "1px solid",
          borderColor:
            theme.palette.divider,

          "&:hover": {
            bgcolor:
              theme.palette
                .action.hover,
          },
        }}
      >
        <DeleteOutlineRoundedIcon
          fontSize="small"
        />
      </IconButton>

      {/* Footer */}

      <Box
        sx={{
          p: 2,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems:
              "center",
            gap: 1,
            minWidth: 0,
          }}
        >
          {isImage ? (
            <ImageOutlinedIcon
              fontSize="small"
            />
          ) : (
            <VideocamOutlinedIcon
              fontSize="small"
            />
          )}

          <Typography
            noWrap
            title={media.name}
            sx={
              TYPOGRAPHY.bodySmall
            }
          >
            {media.name}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}