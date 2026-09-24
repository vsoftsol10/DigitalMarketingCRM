// import {
//   Box,
//   Drawer,
//   IconButton,
//   Stack,
//   Typography,
// } from "@mui/material";

// import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
// import EventNoteRoundedIcon from "@mui/icons-material/EventNoteRounded";

// import { TYPOGRAPHY } from "../../../theme/typography";

// import CalendarEventDetailsHeader from "./CalendarEventDetailsHeader";
// import CalendarEventOverview from "./CalendarEventOverview";
// import CalendarEventCaption from "./CalendarEventCaption";
// import CalendarEventMedia from "./CalendarEventMedia";
// import CalendarEventActions from "./CalendarEventActions";

// export default function CalendarEventDetails({
//   open,
//   event,
//   onClose,
//   onEdit,
//   onReschedule,
//   onPublishNow,
//   onRetry,
//   onDelete,
// }) {
//   if (!event) {
//     return null;
//   }

//   return (
//     <Drawer
//       anchor="right"
//       open={open}
//       onClose={onClose}
//       PaperProps={{
//         sx: {
//           width: { xs: "100%", sm: 480 },
//           maxWidth: 480,
//           display: "flex",
//           flexDirection: "column",
//           bgcolor: "background.paper",
//           boxSizing: "border-box",
//         },
//       }}
//       slotProps={{
//         backdrop: {
//           sx: {
//             bgcolor: "rgba(15, 23, 42, 0.42)",
//           },
//         },
//       }}
//     >
//       {/* ==========================================
//           STICKY TOP BAR
//       ========================================== */}

//       <Box
//         sx={{
//           flexShrink: 0,
//           px: { xs: 2.5, sm: 3 },
//           py: 1.5,
//           borderBottom: "1px solid",
//           borderColor: "divider",
//           bgcolor: "background.paper",
//         }}
//       >
//         <Stack
//           direction="row"
//           alignItems="center"
//           justifyContent="space-between"
//         >
//           <Stack
//             direction="row"
//             alignItems="center"
//             spacing={1}
//           >
//             <EventNoteRoundedIcon
//               sx={{
//                 fontSize: 18,
//                 color: "text.disabled",
//               }}
//             />

//             <Typography
//               sx={{
//                 ...TYPOGRAPHY.caption,
//                 color: "text.secondary",
//                 fontWeight: 700,
//                 textTransform: "uppercase",
//                 letterSpacing: "0.06em",
//               }}
//             >
//               Post details
//             </Typography>
//           </Stack>

//           <IconButton
//             aria-label="Close event details"
//             onClick={onClose}
//             sx={{
//               width: 34,
//               height: 34,
//               borderRadius: 1.75,
//               color: "text.secondary",
//               "&:hover": {
//                 bgcolor: "action.hover",
//                 color: "text.primary",
//               },
//             }}
//           >
//             <CloseRoundedIcon sx={{ fontSize: 20 }} />
//           </IconButton>
//         </Stack>
//       </Box>

//       {/* ==========================================
//           SCROLLABLE CONTENT
//       ========================================== */}

//       <Box
//         sx={{
//           flex: 1,
//           minHeight: 0,
//           overflowY: "auto",
//           px: { xs: 2.5, sm: 3 },
//           pb: 3,
//           "&::-webkit-scrollbar": {
//             width: 6,
//           },
//           "&::-webkit-scrollbar-thumb": {
//             bgcolor: "divider",
//             borderRadius: 10,
//           },
//           "&::-webkit-scrollbar-track": {
//             bgcolor: "transparent",
//           },
//         }}
//       >
//         <CalendarEventDetailsHeader event={event} />
//         <CalendarEventOverview event={event} />
//         <CalendarEventCaption event={event} />
//         <CalendarEventMedia event={event} />
//       </Box>

//       {/* ==========================================
//           STICKY ACTIONS FOOTER
//           Always reachable — no scrolling required to
//           get to the primary action on a post.
//       ========================================== */}

//       <CalendarEventActions
//         event={event}
//         onEdit={onEdit}
//         onReschedule={onReschedule}
//         onPublishNow={onPublishNow}
//         onRetry={onRetry}
//         onDelete={onDelete}
//       />
//     </Drawer>
//   );
// }

import {
  Box,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import EventNoteRoundedIcon from "@mui/icons-material/EventNoteRounded";

import { TYPOGRAPHY } from "../../../theme/typography";

import CalendarEventDetailsHeader from "./CalendarEventDetailsHeader";
import CalendarEventOverview from "./CalendarEventOverview";
import CalendarEventCaption from "./CalendarEventCaption";
import CalendarEventMedia from "./CalendarEventMedia";
import CalendarEventActions from "./CalendarEventActions";

export default function CalendarEventDetails({
  open,
  event,
  onClose,
  onReschedule,
  onPublishNow,
  onRetry,
  onDelete,
  actionLoading,
}) {
  if (!event) {
    return null;
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: "100%", sm: 480 },
          maxWidth: 480,
          height: "100dvh",
          maxHeight: "100dvh",
          display: "flex",
          flexDirection: "column",
          bgcolor: "background.paper",
          boxSizing: "border-box",
        },
      }}
      slotProps={{
        backdrop: {
          sx: {
            bgcolor: "rgba(15, 23, 42, 0.42)",
          },
        },
      }}
    >
      {/* ==========================================
          STICKY TOP BAR
          Close button sits absolutely pinned to the
          top-right corner so it stays put regardless
          of what's in the label row next to it.
      ========================================== */}

      <Box
        sx={{
          position: "relative",
          flexShrink: 0,
          pl: { xs: 2.5, sm: 3 },
          pr: { xs: 6.5, sm: 7 },
          py: 1.75,
          borderBottom: "1px solid",
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Stack
          direction="row"
          alignItems="center"
          spacing={1}
        >
          <EventNoteRoundedIcon
            sx={{
              fontSize: 18,
              color: "text.disabled",
            }}
          />

          <Typography
            sx={{
              ...TYPOGRAPHY.caption,
              color: "text.secondary",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            Post details
          </Typography>
        </Stack>

        <IconButton
          aria-label="Close event details"
          onClick={onClose}
          sx={{
            position: "absolute",
            top: "50%",
            right: { xs: 16, sm: 20 },
            transform: "translateY(-50%)",
            width: 34,
            height: 34,
            borderRadius: "50%",
            color: "text.secondary",
            "&:hover": {
              bgcolor: "action.hover",
              color: "text.primary",
            },
          }}
        >
          <CloseRoundedIcon sx={{ fontSize: 20 }} />
        </IconButton>
      </Box>

      {/* ==========================================
          SCROLLABLE CONTENT
      ========================================== */}

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          overscrollBehavior: "contain",
          px: { xs: 2.5, sm: 3 },
          pb: 3,
          "&::-webkit-scrollbar": {
            width: 6,
          },
          "&::-webkit-scrollbar-thumb": {
            bgcolor: "divider",
            borderRadius: 10,
          },
          "&::-webkit-scrollbar-track": {
            bgcolor: "transparent",
          },
        }}
      >
        <CalendarEventDetailsHeader event={event} />
        <CalendarEventOverview event={event} />
        <CalendarEventCaption event={event} />
        <CalendarEventMedia event={event} />
      </Box>

      {/* ==========================================
          STICKY ACTIONS FOOTER
          Always reachable — no scrolling required to
          get to the primary action on a post.
      ========================================== */}

      <CalendarEventActions
        event={event}
        onReschedule={onReschedule}
        onPublishNow={onPublishNow}
        onRetry={onRetry}
        onDelete={onDelete}
        loading={actionLoading}
      />
    </Drawer>
  );
}
