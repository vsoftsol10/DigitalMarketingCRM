import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import LanguageOutlinedIcon from "@mui/icons-material/LanguageOutlined";

import { PLATFORM_ICONS } from "../../constants/platforms/platformIcons";
import { plannerCardSx } from "./plannerUiSx";

function formatDate(date) {
  if (!date) return "—";

  return new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(time) {
  return typeof time === "string" && time ? time.slice(0, 5) : "—";
}

function formatPlatformName(platform) {
  if (!platform) return "Platform unavailable";

  return platform
    .toLowerCase()
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function groupAccounts(accounts = []) {
  const groups = new Map();

  accounts.forEach((account) => {
    const platform = typeof account?.platform === "string" ? account.platform.trim() : "";
    const key = platform ? platform.toLowerCase() : "__unavailable__";

    if (!groups.has(key)) {
      groups.set(key, { key, platform, accounts: [] });
    }

    groups.get(key).accounts.push(account);
  });

  return [...groups.values()];
}

function DetailField({ label, value, fullWidth = false }) {
  return (
    <Box sx={{ minWidth: 0, gridColumn: fullWidth ? "1 / -1" : undefined }}>
      <Typography sx={{ color: "#94A3B8", fontSize: 13, lineHeight: 1.4 }}>
        {label}
      </Typography>
      <Typography
        sx={{
          mt: 0.4,
          color: "#172554",
          fontSize: 15,
          lineHeight: 1.5,
          fontWeight: 500,
          overflowWrap: "anywhere",
          whiteSpace: "pre-wrap",
        }}
      >
        {value || "—"}
      </Typography>
    </Box>
  );
}

export default function ContentPlannerPostDetailsDialog({ open, idea, onClose }) {
  if (!idea) return null;

  const accountGroups = groupAccounts(idea.selected_social_accounts);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="md"
      scroll="paper"
      aria-labelledby="content-planner-details-title"
      PaperProps={{
        sx: {
          ...plannerCardSx,
          width: { xs: "calc(100% - 24px)", sm: "calc(100% - 48px)" },
          maxHeight: { xs: "calc(100% - 24px)", sm: "calc(100% - 64px)" },
          m: { xs: 1.5, sm: 4 },
          borderRadius: { xs: "16px", sm: "20px" },
          overflow: "hidden",
        },
      }}
    >
      <DialogTitle
        id="content-planner-details-title"
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 2,
          px: { xs: 2, sm: 3 },
          py: 2,
          borderBottom: "1px solid #E5E9F1",
          color: "#172554",
          fontSize: 18,
          fontWeight: 700,
        }}
      >
        Post Details
        <IconButton
          onClick={onClose}
          aria-label="Close post details"
          size="small"
          sx={{
            color: "#64748B",
            borderRadius: "10px",
            "&:hover": { color: "#6941D9", background: "#F5F2FF" },
            "&:focus-visible": { outline: "2px solid rgba(111,145,211,.48)", outlineOffset: 2 },
          }}
        >
          <CloseRoundedIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <DialogContent
        dividers
        sx={{
          p: { xs: 1.5, sm: 2.5 },
          borderColor: "#E5E9F1",
          background: "#F8FAFF",
        }}
      >
        <Stack spacing={2}>
          <Box sx={{ ...plannerCardSx, p: { xs: 2, sm: 3 }, borderRadius: "16px" }}>
            <Typography
              sx={{
                mb: 2,
                color: "#64748B",
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: ".04em",
                textTransform: "uppercase",
              }}
            >
              Post Information
            </Typography>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" },
                gap: { xs: 1.75, sm: 2.25 },
              }}
            >
              <DetailField label="Caption / Post Title" value={idea.caption} />
              {idea.description ? (
                <DetailField label="Description" value={idea.description} fullWidth />
              ) : null}
              <DetailField label="Organization" value={idea.organization} />
              <DetailField label="Post Type" value={idea.content_type || idea.type} />
              <DetailField label="Target Publish Date" value={formatDate(idea.target_publish_date)} />
              <DetailField label="Target Publish Time" value={formatTime(idea.target_publish_time)} />
            </Box>
          </Box>

          <Box sx={{ ...plannerCardSx, p: { xs: 2, sm: 3 }, borderRadius: "16px" }}>
            <Typography
              sx={{
                mb: 2,
                color: "#64748B",
                fontSize: 13,
                fontWeight: 700,
                letterSpacing: ".04em",
                textTransform: "uppercase",
              }}
            >
              Publishing Accounts
            </Typography>

            {accountGroups.length ? (
              <Stack spacing={1.75} divider={<Divider flexItem sx={{ borderColor: "#E9EDF5" }} />}>
                {accountGroups.map((group) => {
                  const PlatformIcon = PLATFORM_ICONS[group.key] || LanguageOutlinedIcon;
                  const platformName = formatPlatformName(group.platform);

                  return (
                    <Box key={group.key} sx={{ minWidth: 0 }}>
                      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                        <Box
                          sx={{
                            width: 34,
                            height: 34,
                            flex: "0 0 auto",
                            display: "grid",
                            placeItems: "center",
                            borderRadius: "10px",
                            color: "#6941D9",
                            background: "#F5F2FF",
                          }}
                        >
                          <PlatformIcon sx={{ fontSize: 19 }} />
                        </Box>
                        <Typography sx={{ color: "#172554", fontSize: 15, fontWeight: 600 }}>
                          {platformName}
                        </Typography>
                        <Typography sx={{ color: "#94A3B8", fontSize: 13 }}>
                          — {group.accounts.length} {group.accounts.length === 1 ? "Account" : "Accounts"}
                        </Typography>
                      </Stack>

                      <Stack spacing={0.6} sx={{ pl: { xs: 1, sm: 5.5 } }}>
                        {group.accounts.map((account, index) => (
                          <Typography
                            key={account.id || `${group.key}-${index}`}
                            sx={{
                              color: "#475569",
                              fontSize: 14,
                              lineHeight: 1.5,
                              overflowWrap: "anywhere",
                            }}
                          >
                            {account.display_name || "—"}
                          </Typography>
                        ))}
                      </Stack>
                    </Box>
                  );
                })}
              </Stack>
            ) : (
              <Typography sx={{ color: "#94A3B8", fontSize: 14 }}>
                No publishing accounts selected.
              </Typography>
            )}
          </Box>
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
