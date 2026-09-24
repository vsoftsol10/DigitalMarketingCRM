import { Box, IconButton, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";

import NotificationIcon from "./NotificationIcon";
import formatActivityDate from "../../utils/date/formatActivityDate";

function formatExpiryDate(value) {
  const date = value ? new Date(`${value}T00:00:00`) : null;
  return date && !Number.isNaN(date.getTime()) ? date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "";
}

export default function NotificationItem({ notification, onClick }) {
  const navigate = useNavigate();
  const isSubscriptionNotification = ["SUBSCRIPTION_EXPIRING", "SUBSCRIPTION_EXPIRED"].includes(notification.type);
  const isExpiring = notification.type === "SUBSCRIPTION_EXPIRING";
  const isFailedPostNotification = notification.type === "FAILED_POST" && Boolean(notification.target_id);
  const isClickable = isSubscriptionNotification || isFailedPostNotification;
  const organizationName = notification.organization_name || "Organization";
  const postSummary = notification.post_title || notification.post_preview;
  const targetSummary = [notification.platform, notification.social_account].filter(Boolean).join(" • ");
  const subscriptionSummary = [
    notification.plan_name,
    notification.expiry_date ? `Expires ${formatExpiryDate(notification.expiry_date)}` : "",
    isExpiring && Number.isInteger(notification.days_remaining) ? `${notification.days_remaining} day${notification.days_remaining === 1 ? "" : "s"} remaining` : "",
  ].filter(Boolean).join(" • ");

  function handleClick() {
    if (isSubscriptionNotification && notification.organization_id) {
      onClick?.(notification);
      navigate(`/organizations/${notification.organization_id}/overview`);
      return;
    }
    if (isFailedPostNotification) {
      onClick?.(notification);
      navigate("/calendar", { state: { targetId: notification.target_id } });
    }
  }

  return (
    <Box onClick={handleClick} sx={{ display: "flex", alignItems: "flex-start", gap: 1.5, px: 2, py: 1.5, borderRadius: "16px", cursor: isClickable ? "pointer" : "default", transition: "0.2s", "&:hover": isClickable ? { bgcolor: "#F8FAFC" } : {} }}>
      <NotificationIcon type={notification.type} />
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography sx={{ fontSize: 15, fontWeight: 600, lineHeight: 1.3, color: "#1E293B" }}>{notification.title}</Typography>
        <Typography sx={{ mt: 0.3, fontSize: 13, color: "#64748B", lineHeight: 1.45 }}>{organizationName}</Typography>
        {isFailedPostNotification && postSummary && <Typography sx={{ mt: 0.4, fontSize: 13, color: "#475569", lineHeight: 1.45, overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{postSummary}</Typography>}
        {isFailedPostNotification && targetSummary && <Typography sx={{ mt: 0.35, fontSize: 12, color: "#94A3B8", lineHeight: 1.4 }}>{targetSummary}</Typography>}
        {isFailedPostNotification && notification.failure_reason && <Typography sx={{ mt: 0.35, fontSize: 12, color: "#64748B", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{notification.failure_reason}</Typography>}
        {isSubscriptionNotification && subscriptionSummary && <Typography sx={{ mt: 0.4, fontSize: 12, color: "#64748B", lineHeight: 1.4 }}>{subscriptionSummary}</Typography>}
      </Box>
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 0.5, flexShrink: 0 }}>
        <Typography sx={{ fontSize: 12, fontWeight: 500, color: "#94A3B8", whiteSpace: "nowrap" }}>{formatActivityDate(notification.created_at)}</Typography>
        {isClickable && <IconButton size="small" sx={{ color: "#94A3B8", p: 0.25 }}><ArrowForwardRoundedIcon sx={{ fontSize: 18 }} /></IconButton>}
      </Box>
    </Box>
  );
}
