import { Paper, Box, Typography } from "@mui/material";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import TuneOutlinedIcon from "@mui/icons-material/TuneOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import EditNoteOutlinedIcon from "@mui/icons-material/EditNoteOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";

import { TYPOGRAPHY } from "../../../theme/typography";
import { postCardSx, postFormFieldSx } from "./postUiSx";

const sectionIcons = {
  Organization: BusinessOutlinedIcon,
  "Upload Media": ImageOutlinedIcon,
  "Publishing Accounts": GroupsOutlinedIcon,
  "Content Type": TuneOutlinedIcon,
  "AI Caption Assistant": AutoAwesomeOutlinedIcon,
  Caption: EditNoteOutlinedIcon,
  Publishing: ScheduleOutlinedIcon,
};

export default function SectionCard({
  title,
  description,
  children,
  compact = false,
}) {
  const SectionIcon = sectionIcons[title];

  return (
    <Paper
      elevation={0}
      sx={{
        ...postCardSx,
        p: { xs: 2, sm: compact ? 2.25 : 2.5 },
        color: "#17284D",
        ...postFormFieldSx,
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          mb: compact ? 1.75 : 2.25,
        }}
      >
        {SectionIcon && (
          <Box
            aria-hidden="true"
            sx={{
              width: 38,
              height: 38,
              flexShrink: 0,
              borderRadius: "11px",
              display: "grid",
              placeItems: "center",
              color: "#6941D9",
              background: "#F3F0FF",
              border: "1px solid #E7E1FF",
            }}
          >
            <SectionIcon sx={{ fontSize: 20 }} />
          </Box>
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ ...TYPOGRAPHY.sectionTitle, color: "#17284D", fontSize: 17 }}>
            {title}
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.sectionDescription,
              mt: 0.25,
              color: "#71809F",
            }}
          >
            {description}
          </Typography>
        </Box>
      </Box>

      {children}
    </Paper>
  );
}
