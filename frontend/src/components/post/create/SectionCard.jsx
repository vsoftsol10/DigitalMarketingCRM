import { Paper, Box, Typography } from "@mui/material";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import TuneOutlinedIcon from "@mui/icons-material/TuneOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import EditNoteOutlinedIcon from "@mui/icons-material/EditNoteOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";

import { TYPOGRAPHY } from "../../../theme/typography";
import overviewGlassCardSx from "../../organization/overview/overviewGlassCardSx";

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
        ...overviewGlassCardSx,
        p: compact ? 2.5 : 3,
        color: "#17284D",
        "& .MuiOutlinedInput-root": {
          minHeight: 50,
          borderRadius: "15px",
          background:
            "linear-gradient(145deg, rgba(255,255,255,.88), rgba(239,245,255,.82))",
          boxShadow:
            "inset 0 2px 5px rgba(101,122,169,.08), 0 3px 9px rgba(75,96,151,.08), inset 0 1px 0 rgba(255,255,255,.95)",
          "& fieldset": { borderColor: "rgba(255,255,255,.92)" },
          "&:hover fieldset": { borderColor: "rgba(153,174,220,.72)" },
          "&.Mui-focused fieldset": {
            borderColor: "#8C9EEB",
            borderWidth: "1px",
          },
        },
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          mb: compact ? 2 : 3,
        }}
      >
        {SectionIcon && (
          <Box
            aria-hidden="true"
            sx={{
              width: 46,
              height: 46,
              flexShrink: 0,
              borderRadius: "50%",
              display: "grid",
              placeItems: "center",
              color: "#557FE1",
              background:
                "linear-gradient(145deg, rgba(255,255,255,.96), rgba(220,232,255,.86))",
              border: "1px solid rgba(255,255,255,.95)",
              boxShadow:
                "0 6px 12px rgba(80,101,164,.15), inset 0 2px 0 rgba(255,255,255,.98), inset 0 -2px 4px rgba(104,124,175,.1)",
            }}
          >
            <SectionIcon sx={{ fontSize: 23 }} />
          </Box>
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ ...TYPOGRAPHY.sectionTitle, color: "#17284D" }}>
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
