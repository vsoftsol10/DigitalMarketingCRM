import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Badge,
  Box,
  IconButton,
  Popover,
  Typography,
} from "@mui/material";
import NotificationsNoneOutlinedIcon from "@mui/icons-material/NotificationsNoneOutlined";
import { useNavigate } from "react-router-dom";

import NotificationIcon from "../dashboard/NotificationIcon";
import formatActivityDate from "../../utils/date/formatActivityDate";
import { useAuthContext } from "../../context/AuthContext";
import notificationService, { NOTIFICATION_QUERY_KEY } from "../../services/notification.service";

export default function HeaderNotificationCenter() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthContext();
  const [anchorEl, setAnchorEl] = useState(null);
  const notificationQueryKey = [
    ...NOTIFICATION_QUERY_KEY,
    user?.id || user?.email || "anonymous",
  ];
  const {
    data: notificationData,
    isError,
    isFetching,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: notificationQueryKey,
    queryFn: notificationService.getNotifications,
    enabled: Boolean(user),
    refetchOnMount: "always",
    refetchInterval: 60000,
  });
  const notifications = notificationData?.notifications || [];
  const unreadCount = notificationData?.unread_count || 0;
  const loading = notifications.length === 0 && (isLoading || isFetching);

  async function openCenter(event) {
    setAnchorEl(event.currentTarget);
    if (!isFetching && !queryClient.isFetching({ queryKey: notificationQueryKey })) {
      await refetch();
    }
  }

  function openNotification(notification) {
    void queryClient.cancelQueries({
      queryKey: notificationQueryKey,
      exact: true,
    });
    queryClient.setQueryData(notificationQueryKey, (current) => {
      if (!current) return current;

      return {
        ...current,
        notifications: (current.notifications || []).filter(
          (item) => item.id !== notification.id,
        ),
        unread_count: notification.is_read
          ? current.unread_count || 0
          : Math.max(0, (current.unread_count || 0) - 1),
      };
    });
    setAnchorEl(null);

    if (["FAILED_POST", "POST_PUBLISHED"].includes(notification.type) && notification.target_id) {
      navigate("/calendar", { state: { targetId: notification.target_id } });
    } else if (notification.organization_id) {
      navigate(`/organizations/${notification.organization_id}/overview`);
    }

    if (!notification.is_read) {
      void notificationService.markAsRead(notification.id).catch(() => {});
    }
  }

  const isOpen = Boolean(anchorEl);

  return (
    <>
      <IconButton
        aria-label="Notifications"
        aria-haspopup="true"
        aria-expanded={isOpen ? "true" : undefined}
        onClick={openCenter}
      >
        <Badge
          color="error"
          variant="dot"
          overlap="circular"
          invisible={unreadCount === 0}
        >
          <NotificationsNoneOutlinedIcon sx={{ fontSize: 24, color: "#475569" }} />
        </Badge>
      </IconButton>
      <Popover
        open={isOpen}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              width: "min(380px, calc(100vw - 24px))",
              minWidth: "min(380px, calc(100vw - 24px))",
              maxWidth: "min(380px, calc(100vw - 24px))",
              height: "min(514px, calc(100vh - 24px))",
              minHeight: "min(514px, calc(100vh - 24px))",
              maxHeight: "min(514px, calc(100vh - 24px))",
              boxSizing: "border-box",
              mt: 1,
              borderRadius: 2,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            },
          },
        }}
      >
        <Box
          sx={{
            height: 74,
            boxSizing: "border-box",
            flexShrink: 0,
            px: 2,
            py: 1.75,
            borderBottom: "1px solid #E2E8F0",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <Typography sx={{ fontSize: 16, fontWeight: 700, color: "#1E293B" }}>
            Notifications
          </Typography>
          <Typography
            aria-hidden={unreadCount === 0}
            sx={{
              mt: 0.25,
              height: 18,
              fontSize: 12,
              lineHeight: "18px",
              color: "#64748B",
              visibility: unreadCount > 0 ? "visible" : "hidden",
            }}
          >
            {unreadCount} unread
          </Typography>
        </Box>
        <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
          {loading && notifications.length === 0 ? (
            <Typography
              sx={{
                height: "100%",
                px: 2,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                textAlign: "center",
                fontSize: 14,
                color: "#64748B",
              }}
            >
              Loading notifications…
            </Typography>
          ) : notifications.length === 0 ? (
            <Typography
              sx={{
                height: "100%",
                px: 2,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                textAlign: "center",
                fontSize: 14,
                color: "#64748B",
              }}
            >
              {isError ? "Unable to load notifications" : "No new notifications"}
            </Typography>
          ) : notifications.map((notification) => (
            <Box
              key={notification.id}
              component="button"
              type="button"
              onClick={() => openNotification(notification)}
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1.25,
                width: "100%",
                px: 1.75,
                py: 1.5,
                border: 0,
                borderBottom: "1px solid #F1F5F9",
                textAlign: "left",
                bgcolor: notification.is_read ? "#FFFFFF" : "#F8FAFC",
                cursor: "pointer",
                "&:hover": { bgcolor: "#F1F5F9" },
              }}
            >
              <NotificationIcon type={notification.type} />
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography sx={{ fontSize: 13, fontWeight: notification.is_read ? 500 : 700, color: "#1E293B" }}>
                  {notification.title}
                </Typography>
                <Typography sx={{ mt: 0.25, fontSize: 12, color: "#64748B" }}>
                  {notification.organization_name}
                </Typography>
                <Typography sx={{ mt: 0.25, fontSize: 12, color: "#475569", lineHeight: 1.4 }}>
                  {notification.post_title || notification.message}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 0.5, flexShrink: 0 }}>
                <Typography sx={{ fontSize: 11, color: "#94A3B8", whiteSpace: "nowrap" }}>
                  {formatActivityDate(notification.created_at)}
                </Typography>
                {!notification.is_read && <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: "#EF4444" }} />}
              </Box>
            </Box>
          ))}
        </Box>
      </Popover>
    </>
  );
}
