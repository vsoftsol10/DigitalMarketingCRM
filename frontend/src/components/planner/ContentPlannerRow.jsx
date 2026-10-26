import { Box, Chip, TableCell, TableRow, Typography } from "@mui/material";
import ContentPlannerActionMenu from "./ContentPlannerActionMenu";
import { Stack } from "@mui/material";
import { useNavigate } from "react-router-dom";

function formatTargetDateTime(date, time) {
  if (!date) {
    return "—";
  }
  const formattedDate = new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
  return time ? `${formattedDate} • ${time.slice(0, 5)}` : formattedDate;
}

export default function ContentPlannerRow({ idea, onDelete }) {
  const navigate = useNavigate();
  return (
    <TableRow
      hover
      sx={{
        "& td": {
          borderBottom: "1px solid rgba(146,168,201,.22)",
          py: 2.5,
          background:
            "linear-gradient(145deg, rgba(250,252,255,.82), rgba(237,245,255,.68))",
          boxShadow:
            "inset 0 1px 0 rgba(255,255,255,.9), inset 0 -1px 2px rgba(112,127,177,.05)",
        },

        "&:hover td": {
          background:
            "linear-gradient(145deg, rgba(242,247,255,.96), rgba(228,239,255,.82))",
        },

        "&:last-child td": {
          borderBottom: "none",
        },
      }}
    >
      {/* Caption */}

      <TableCell>
        <Box
            sx={{
              minWidth: 0,
            }}
          >
            <Typography
              sx={{
                fontSize: 15,
                fontWeight: 600,
                color: "#17294F",
              }}
            >
              {idea.caption}
            </Typography>

            <Typography
              sx={{
                mt: 0.5,

                fontSize: 13,

                color: "#657899",

                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",

                maxWidth: 320,
              }}
            >
              {idea.description}
            </Typography>
        </Box>
      </TableCell>

      {/* Organization */}

      <TableCell>
        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 500,
            color: "#304563",
          }}
        >
          {idea.organization}
        </Typography>
      </TableCell>

      {/* Publish accounts */}

      <TableCell>
        <Stack spacing={0.5}>
          {(idea.selected_social_accounts || []).map((account) => (
            <Typography key={account.id} noWrap sx={{ fontSize: 13, color: "#536A8A" }}>
              {account.display_name} · {String(account.platform || "").toLowerCase()}
            </Typography>
          ))}
          {!idea.selected_social_accounts?.length && (
            <Typography sx={{ fontSize: 13, color: "#8294B4" }}>No accounts selected</Typography>
          )}
        </Stack>
      </TableCell>

      {/* Type */}

      <TableCell>
        <Chip
          label={idea.content_type || idea.type}
          size="small"
          sx={{
            background: "linear-gradient(145deg, rgba(238,245,255,.96), rgba(222,234,252,.86))",
            color: "#536A8A",
            fontWeight: 600,
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,.86)",
          }}
        />
      </TableCell>

      {/* Target date and time */}

      <TableCell>
        <Typography
          sx={{
            fontSize: 14,
            color: "#657899",
            width: 160,
            whiteSpace: "nowrap",
          }}
        >
          {formatTargetDateTime(idea.target_publish_date, idea.target_publish_time)}
        </Typography>
      </TableCell>

      {/* Action */}

      <TableCell align="center">
        <ContentPlannerActionMenu
          onEdit={() => navigate(`/planner/${idea.id}/edit`)}
          onDelete={() => onDelete(idea)}
          onCreatePost={() =>
            navigate("/posts", {
              state: {
                plannerPrefill: {
                  organization: idea.organization_code,
                  socialAccountIds: (idea.selected_social_accounts || []).map(
                    (account) => account.id,
                  ),
                  contentType: idea.content_type || idea.type,
                  caption: idea.caption || "",
                  publishDate: idea.target_publish_date || "",
                  publishTime: idea.target_publish_time || "",
                },
              },
            })
          }
        />
      </TableCell>
    </TableRow>
  );
}
