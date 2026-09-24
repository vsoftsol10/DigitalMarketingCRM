import { Box, Typography } from "@mui/material";

import ActivityIcon from "./ActivityIcon";
import formatActivityDate from "../../utils/date/formatActivityDate";

const ACTIVITY_MESSAGES = {
  ORGANIZATION_CREATED: "Organization created", SUBSCRIPTION_ACTIVATED: "Subscription activated",
  SUBSCRIPTION_RENEWED: "Subscription renewed", SUBSCRIPTION_CANCELLED: "Subscription cancelled",
  POST_CREATED: "Post created", POST_SCHEDULED: "Post scheduled",
  POST_PUBLISHED: "Post published", POST_FAILED: "Post failed",
};
const POST_EVENTS = new Set(["POST_CREATED", "POST_SCHEDULED", "POST_PUBLISHED", "POST_FAILED"]);
const SUBSCRIPTION_EVENTS = new Set(["SUBSCRIPTION_ACTIVATED", "SUBSCRIPTION_RENEWED", "SUBSCRIPTION_CANCELLED"]);

function formatDateTime(value) {
  const date = value ? new Date(value) : null;
  return date && !Number.isNaN(date.getTime()) ? date.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "";
}

function formatDate(value) {
  const date = value ? new Date(`${value}T00:00:00`) : null;
  return date && !Number.isNaN(date.getTime()) ? date.toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "";
}

export default function ActivityItem({ activity, onClick }) {
  const eventType = activity.event_type || activity.type;
  const actor = activity.actor_name || activity.actor_email;
  const organizationName = activity.organization_name || "Organization";
  const isPostEvent = POST_EVENTS.has(eventType);
  const isSubscriptionEvent = SUBSCRIPTION_EVENTS.has(eventType);
  const postSummary = activity.post_title || activity.post_preview;
  const targetSummary = [activity.platform, activity.social_account].filter(Boolean).join(" • ");
  const eventTime = eventType === "POST_PUBLISHED" ? formatDateTime(activity.published_at) : formatDateTime(activity.scheduled_at);
  const subscriptionSummary = [activity.plan_name, activity.expiry_date ? `Expires ${formatDate(activity.expiry_date)}` : ""].filter(Boolean).join(" • ");

  return (
    <Box onClick={() => onClick?.(activity)} sx={{ display: "flex", alignItems: "flex-start", gap: 2, px: 2, py: 1.5, minHeight: { xs: 132, sm: 116 }, borderRadius: "16px", cursor: onClick ? "pointer" : "default", transition: "background-color 0.2s ease", "&:hover": onClick ? { bgcolor: "#F8FAFC" } : {} }}>
      <ActivityIcon type={eventType} />
      <Box sx={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <Typography sx={{ fontSize: 15, fontWeight: 600, color: "#1E293B", lineHeight: 1.35 }}>{ACTIVITY_MESSAGES[eventType] || "Activity updated"}</Typography>
        <Typography sx={{ mt: 0.3, fontSize: 13, color: "#64748B", lineHeight: 1.45 }}>{actor ? `${organizationName} • ${actor}` : organizationName}</Typography>
        {isPostEvent && postSummary && <Typography sx={{ mt: 0.45, fontSize: 13, color: "#475569", lineHeight: 1.45, overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{postSummary}</Typography>}
        {isPostEvent && (targetSummary || eventTime) && <Typography sx={{ mt: 0.35, fontSize: 12, color: "#94A3B8", lineHeight: 1.4 }}>{[targetSummary, eventTime].filter(Boolean).join(" • ")}</Typography>}
        {isSubscriptionEvent && subscriptionSummary && <Typography sx={{ mt: 0.45, fontSize: 12, color: "#94A3B8", lineHeight: 1.4 }}>{subscriptionSummary}</Typography>}
      </Box>
      <Typography sx={{ flexShrink: 0, ml: 1, fontSize: 12, fontWeight: 500, color: "#94A3B8", whiteSpace: "nowrap" }}>{formatActivityDate(activity.occurred_at)}</Typography>
    </Box>
  );
}
