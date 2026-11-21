import { Box, Button, Chip, TableCell, TableRow, Tooltip, Typography } from "@mui/material";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import LanguageOutlinedIcon from "@mui/icons-material/LanguageOutlined";
import ContentPlannerActionMenu from "./ContentPlannerActionMenu";
import { Stack } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { PLATFORM_ICONS } from "../../constants/platforms/platformIcons";
import { PLATFORM_COLORS } from "../../constants/platforms/platformColors";

function formatTargetDateTime(date, time) {
  if (!date) {
    return "—";
  }
  const formattedDate = new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
  return time ? `${formattedDate} • ${time.slice(0, 5)}` : formattedDate;
}

export default function ContentPlannerRow({ idea, onDelete, onView }) {
  const navigate = useNavigate();
  const platforms = [...new Map(
    (idea.selected_social_accounts || [])
      .filter((account) => typeof account?.platform === "string" && account.platform.trim())
      .map((account) => [account.platform.trim().toLowerCase(), account.platform.trim()]),
  ).entries()];

  return (
    <TableRow
      hover
      sx={{
        "& td": {
          borderBottom: "1px solid #E5E9F1",
          py: 2.5,
          background: "#FFFFFF",
          boxShadow: "none",
        },

        "&:hover td": {
          background: "#F8FAFC",
        },

        "&:last-child td": {
          borderBottom: "none",
        },
      }}
    >
      {/* Caption */}

      <TableCell data-label="Caption">
        <Box sx={{ minWidth: 0, maxWidth: "100%" }}>
            <Typography
              sx={{
                fontSize: 15,
                fontWeight: 600,
                color: "#172554",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {idea.caption || "—"}
            </Typography>

            <Typography
              sx={{
                mt: 0.5,

                fontSize: 13,

                color: "#657899",

                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                maxWidth: "100%",
                display: "block",
              }}
            >
              {idea.description || ""}
            </Typography>
        </Box>
      </TableCell>

      {/* Organization */}

      <TableCell data-label="Organization">
        <Typography
          sx={{
            fontSize: 14,
            fontWeight: 500,
            color: "#475569",
            overflowWrap: "anywhere",
          }}
        >
          {idea.organization}
        </Typography>
      </TableCell>

      {/* Platforms */}

      <TableCell data-label="Platform">
        <Stack direction="row" alignItems="center" spacing={0.75} sx={{ minHeight: 28 }}>
          {platforms.length ? platforms.map(([key, label]) => {
            const PlatformIcon = PLATFORM_ICONS[key] || LanguageOutlinedIcon;
            const iconColor = PLATFORM_COLORS[key]?.iconColor || "#667995";
            return (
              <Tooltip key={key} title={label}>
                <Box
                  component="span"
                  aria-label={label}
                  sx={{ display: "inline-flex", alignItems: "center", color: iconColor }}
                >
                  <PlatformIcon sx={{ fontSize: 19 }} />
                </Box>
              </Tooltip>
            );
          }) : (
            <Typography sx={{ fontSize: 13, color: "#94A3B8" }}>—</Typography>
          )}
        </Stack>
      </TableCell>

      {/* Type */}

      <TableCell data-label="Type">
        <Chip
          label={idea.content_type || idea.type}
          size="small"
          sx={{
            background: "#F5F2FF",
            color: "#6941D9",
            fontWeight: 600,
            borderRadius: "8px",
            border: "1px solid #E5DDFC",
          }}
        />
      </TableCell>

      {/* Target date and time */}

      <TableCell data-label="Target date & time">
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

      <TableCell align="center" data-label="Actions">
        <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.5}>
          <Button
            type="button"
            size="small"
            startIcon={<VisibilityOutlinedIcon sx={{ fontSize: 18 }} />}
            onClick={() => onView?.(idea)}
            aria-label={`View ${idea.caption || "content idea"}`}
            sx={{
              minWidth: 0,
              px: 0.75,
              py: 0.5,
              borderRadius: "9px",
              color: "#475569",
              textTransform: "none",
              fontSize: 13,
              fontWeight: 600,
              whiteSpace: "nowrap",
              "& .MuiButton-startIcon": { mr: 0.5 },
              "&:hover": { color: "#6941D9", background: "#F5F2FF" },
              "&:focus-visible": { outline: "2px solid rgba(111,145,211,.48)", outlineOffset: 2 },
            }}
          >
            View
          </Button>
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
        </Stack>
      </TableCell>
    </TableRow>
  );
}
