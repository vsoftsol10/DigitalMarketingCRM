import { Box, Chip, TableCell, TableRow, Typography } from "@mui/material";
import PlatformBadge from "../insights/PlatformBadge";
import ContentPlannerActionMenu from "./ContentPlannerActionMenu";
import { Stack } from "@mui/material";
import ContentIdeaIcon from "./ContentIdeaIcon";
import { useNavigate } from "react-router-dom";

export default function ContentPlannerRow({ idea, onDelete }) {
  const navigate = useNavigate();
  return (
    <TableRow
      hover
      sx={{
        "& td": {
          borderBottom: "1px solid #F1F5F9",
          py: 2.5,
        },

        "&:last-child td": {
          borderBottom: "none",
        },
      }}
    >
      {/* Idea */}

      <TableCell>
        <Stack direction="row" spacing={2} alignItems="center">
          <ContentIdeaIcon platform={idea.platform} />

          <Box
            sx={{
              minWidth: 0,
            }}
          >
            <Typography
              sx={{
                fontSize: 15,
                fontWeight: 600,
                color: "#0F172A",
              }}
            >
              {idea.title}
            </Typography>

            <Typography
              sx={{
                mt: 0.5,

                fontSize: 13,

                color: "#64748B",

                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",

                maxWidth: 320,
              }}
            >
              {idea.description}
            </Typography>
          </Box>
        </Stack>
      </TableCell>

      {/* Organization */}

      <TableCell>
        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 500,
            color: "#334155",
          }}
        >
          {idea.organization}
        </Typography>
      </TableCell>

      {/* Platform */}

      <TableCell>
        <PlatformBadge platform={idea.platform} />
      </TableCell>

      {/* Type */}

      <TableCell>
        <Chip
          label={idea.type}
          size="small"
          sx={{
            bgcolor: "#F8FAFC",
            color: "#475569",
            fontWeight: 600,
            borderRadius: "8px",
          }}
        />
      </TableCell>

      {/* Goal */}

      <TableCell>
        <Typography
          sx={{
            fontSize: 14,
            color: "#334155",
          }}
        >
          {idea.goal}
        </Typography>
      </TableCell>

      {/* Date */}

      <TableCell>
        <Typography
          sx={{
            fontSize: 14,
            color: "#64748B",
            width: 130,
            whiteSpace: "nowrap",
          }}
        >
          {idea.target_publish_date}
        </Typography>
      </TableCell>

      {/* Action */}

      <TableCell align="center">
        <ContentPlannerActionMenu
          onEdit={() => navigate(`/planner/${idea.id}/edit`)}
          onDelete={() => onDelete(idea)}
          onCreatePost={() => console.log("Create Post", idea.id)}
        />
      </TableCell>
    </TableRow>
  );
}
