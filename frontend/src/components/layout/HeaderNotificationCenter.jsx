import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Badge,
  Box,
  Button,
  IconButton,
  Popover,
  Typography,
} from "@mui/material";
import NotificationsNoneOutlinedIcon from "@mui/icons-material/NotificationsNoneOutlined";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import NotificationIcon from "../dashboard/NotificationIcon";
import formatActivityDate from "../../utils/date/formatActivityDate";
import { useAuthContext } from "../../context/AuthContext";
import notificationService, { NOTIFICATION_QUERY_KEY } from "../../services/notification.service";

export default function HeaderNotificationCenter() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthContext();
  const [anchorEl, setAnchorEl] = useState(null);
  const [isClearing, setIsClearing] = useState(false);
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
    if (!isClearing && !isFetching && !queryClient.isFetching({ queryKey: notificationQueryKey })) {
      await refetch();
    }
  }

  async function clearAllNotifications() {
    if (isClearing || notifications.length === 0) return;

    setIsClearing(true);

    try {
      await queryClient.cancelQueries({ queryKey: notificationQueryKey, exact: true });
      await notificationService.clearAll();
      await queryClient.cancelQueries({ queryKey: notificationQueryKey, exact: true });
      queryClient.setQueryData(notificationQueryKey, (current) => current
        ? { ...current, notifications: [], unread_count: 0 }
        : current);
    } catch {
      toast.error("Unable to clear notifications. Please try again.");
    } finally {
      setIsClearing(false);
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
        sx={{
          width: 44,
          height: 44,
          color: "#52627F",
          border: "1px solid rgba(255,255,255,.92)",
          background: "linear-gradient(145deg, rgba(247,250,255,.94), rgba(232,239,252,.86))",
          boxShadow: "0 6px 14px rgba(88, 106, 160, .12), inset 0 2px 2px rgba(255,255,255,.95), inset 0 -1px 2px rgba(94,111,159,.06)",
          "&:hover": { background: "linear-gradient(145deg, rgba(240,246,255,.98), rgba(224,235,253,.94))" },
          "&:focus-visible": { outline: "2px solid rgba(89,116,220,.5)", outlineOffset: 2 },
        }}
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
              border: "1px solid rgba(255,255,255,.94)",
              borderRadius: "18px",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              background: "linear-gradient(145deg, rgba(249,252,255,.99), rgba(236,243,255,.97))",
              boxShadow: "0 18px 38px rgba(62,82,140,.2), 0 5px 12px rgba(62,82,140,.09), inset 0 1px 0 rgba(255,255,255,.98)",
              backdropFilter: "blur(18px)",
            },
          },
        }}
      >
        <Box
          sx={{
            height: 74,
            boxSizing: "border-box",
            flexShrink: 0,
            px: 2.25,
            py: 1.75,
            borderBottom: "1px solid rgba(126,146,190,.2)",
            background: "linear-gradient(145deg, rgba(242,247,255,.98), rgba(235,242,255,.94))",
            boxShadow: "inset 0 1px 0 rgba(255,255,255,.98)",
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 1,
          }}
        >
          <Box sx={{ minWidth: 0 }}>
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
          <Button
            size="small"
            onClick={clearAllNotifications}
            disabled={isClearing || notifications.length === 0}
            sx={{
              flexShrink: 0,
              minWidth: 0,
              px: 1,
              color: "#5269B4",
              fontSize: 12,
              fontWeight: 600,
              textTransform: "none",
              whiteSpace: "nowrap",
              borderRadius: 1.5,
              "&:hover": { background: "rgba(89,116,220,.08)" },
              "&.Mui-disabled": { color: "#94A3B8" },
            }}
          >
            {isClearing ? "Clearing…" : "Clear all"}
          </Button>
        </Box>
        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            overscrollBehavior: "contain",
            scrollbarWidth: "thin",
            scrollbarColor: "rgba(122,143,190,.42) transparent",
            "&::-webkit-scrollbar": { width: 7 },
            "&::-webkit-scrollbar-thumb": { borderRadius: 8, background: "rgba(122,143,190,.36)" },
          }}
        >
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
                color: "#71809D",
                background: "rgba(246,249,255,.6)",
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
                color: "#71809D",
                background: "rgba(246,249,255,.6)",
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
                borderBottom: "1px solid rgba(126,146,190,.16)",
                textAlign: "left",
                color: "#263754",
                background: notification.is_read
                  ? "rgba(250,252,255,.72)"
                  : "rgba(231,239,255,.82)",
                cursor: "pointer",
                font: "inherit",
                "&:hover": { background: "rgba(222,234,255,.92)" },
                "&:focus-visible": {
                  outline: "2px solid rgba(89,116,220,.48)",
                  outlineOffset: -2,
                  background: "rgba(222,234,255,.92)",
                },
              }}
            >
              <NotificationIcon type={notification.type} raised />
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
