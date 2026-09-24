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
          borderBottom: "1px solid #F1F5F9",
          py: 2.5,
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
                color: "#0F172A",
              }}
            >
              {idea.caption}
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

      {/* Publish accounts */}

      <TableCell>
        <Stack spacing={0.5}>
          {(idea.selected_social_accounts || []).map((account) => (
            <Typography key={account.id} noWrap sx={{ fontSize: 13, color: "#475569" }}>
              {account.display_name} · {String(account.platform || "").toLowerCase()}
            </Typography>
          ))}
          {!idea.selected_social_accounts?.length && (
            <Typography sx={{ fontSize: 13, color: "#94A3B8" }}>No accounts selected</Typography>
          )}
        </Stack>
      </TableCell>

      {/* Type */}

      <TableCell>
        <Chip
          label={idea.content_type || idea.type}
          size="small"
          sx={{
            bgcolor: "#F8FAFC",
            color: "#475569",
            fontWeight: 600,
            borderRadius: "8px",
          }}
        />
      </TableCell>

      {/* Target date and time */}

      <TableCell>
        <Typography
          sx={{
            fontSize: 14,
            color: "#64748B",
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
