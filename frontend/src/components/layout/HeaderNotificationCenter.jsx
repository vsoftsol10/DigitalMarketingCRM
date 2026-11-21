import { useRef, useState } from "react";
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
import LoadingSpinner from "../ui/LoadingSpinner";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";
import formatActivityDate from "../../utils/date/formatActivityDate";
import { useAuthContext } from "../../context/AuthContext";
import notificationService, { NOTIFICATION_QUERY_KEY } from "../../services/notification.service";

export default function HeaderNotificationCenter() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthContext();
  const [anchorEl, setAnchorEl] = useState(null);
  const [isClearing, setIsClearing] = useState(false);
  const pendingReadIdsRef = useRef(new Set());
  const notificationQueryKey = [
    ...NOTIFICATION_QUERY_KEY,
    user?.id || user?.email || "anonymous",
  ];
  const {
    data: notificationData,
    isError,
    isFetching,
    isLoading,
    error: notificationQueryError,
    refetch,
  } = useQuery({
    queryKey: notificationQueryKey,
    queryFn: async () => {
      const response = await notificationService.getNotifications();
      if (
        !response
        || !Array.isArray(response.notifications)
        || !Number.isFinite(response.unread_count)
      ) {
        throw new Error("Notification data was not returned in the expected format.");
      }
      return response;
    },
    enabled: Boolean(user),
    refetchOnMount: "always",
    refetchInterval: 60000,
  });
  const hasNotificationData = Boolean(
    notificationData
    && Array.isArray(notificationData.notifications)
    && Number.isFinite(notificationData.unread_count),
  );
  const notifications = hasNotificationData ? notificationData.notifications : [];
  const unreadCount = hasNotificationData ? notificationData.unread_count : 0;
  const loading = !hasNotificationData && (isLoading || isFetching);

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

  async function openNotification(notification) {
    const notificationId = notification?.id;
    if (!notificationId || pendingReadIdsRef.current.has(notificationId)) return;

    pendingReadIdsRef.current.add(notificationId);

    try {
      await queryClient.cancelQueries({
        queryKey: notificationQueryKey,
        exact: true,
      });

      const previousData = queryClient.getQueryData(notificationQueryKey);
      let optimisticData = null;
      if (previousData) {
        optimisticData = queryClient.setQueryData(notificationQueryKey, {
          ...previousData,
          notifications: (previousData.notifications || []).filter(
            (item) => item.id !== notificationId,
          ),
          unread_count: notification.is_read
            ? previousData.unread_count || 0
            : Math.max(0, (previousData.unread_count || 0) - 1),
        });
      }
      setAnchorEl(null);

      if (["FAILED_POST", "POST_PUBLISHED"].includes(notification.type) && notification.target_id) {
        navigate("/calendar", { state: { targetId: notification.target_id } });
      } else if (notification.organization_id) {
        navigate(`/organizations/${notification.organization_id}/overview`);
      }

      if (!notification.is_read) {
        try {
          await notificationService.markAsRead(notificationId);
        } catch {
          if (previousData && optimisticData) {
            queryClient.setQueryData(notificationQueryKey, (current) => (
              current === optimisticData ? previousData : current
            ));
          }
          toast.error("Unable to mark this notification as read. Please try again.");
        }
      }
    } finally {
      pendingReadIdsRef.current.delete(notificationId);
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
          border: "1px solid #E1E5F0",
          background: "#FFFFFF",
          boxShadow: "0 3px 8px rgba(31,41,80,.06)",
          "&:hover": { background: "#F8FAFC" },
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
              width: "min(360px, calc(100vw - 24px))",
              minWidth: 0,
              maxWidth: "min(360px, calc(100vw - 24px))",
              maxHeight: "min(560px, calc(100vh - 96px))",
              boxSizing: "border-box",
              mt: 1,
              border: "1px solid #E2E8F0",
              borderRadius: "18px",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              background: "#FFFFFF",
              boxShadow: "0 8px 22px rgba(31,41,80,.10)",
            },
          },
        }}
      >
        <Box
          sx={{
            minHeight: 74,
            boxSizing: "border-box",
            flexShrink: 0,
            px: { xs: 1.75, sm: 2.25 },
            py: 1.5,
            borderBottom: "1px solid #E5E7EB",
            background: "#FFFFFF",
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 1,
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ fontSize: 16, fontWeight: 700, color: "#172554" }}>
              Notifications
            </Typography>
            <Typography
              aria-hidden={unreadCount === 0}
              sx={{
                mt: 0.25,
                height: 18,
                fontSize: 12,
                lineHeight: "18px",
                color: "#7B89A2",
                visibility: unreadCount > 0 ? "visible" : "hidden",
              }}
            >
              {unreadCount} unread
            </Typography>
          </Box>
          <Box
            sx={{
              width: 18,
              height: 18,
              flex: "0 0 18px",
              display: "grid",
              placeItems: "center",
            }}
          >
            {isFetching && hasNotificationData && (
              <LoadingSpinner size={16} ariaLabel="Updating notifications" />
            )}
          </Box>
          <Button
            size="small"
            onClick={clearAllNotifications}
            disabled={isClearing || notifications.length === 0}
            sx={{
              flexShrink: 0,
              minWidth: 0,
              px: 1,
              color: "#6941D9",
              fontSize: 13,
              fontWeight: 600,
              textTransform: "none",
              whiteSpace: "nowrap",
              borderRadius: "10px",
              "&:hover": { background: "#F5F2FF" },
              "&.Mui-disabled": { color: "#94A3B8" },
              "&:focus-visible": { outline: "2px solid rgba(111,145,211,.48)", outlineOffset: 2 },
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
            scrollbarColor: "rgba(122,143,190,.38) transparent",
            "&::-webkit-scrollbar": { width: 7 },
            "&::-webkit-scrollbar-thumb": { borderRadius: 8, background: "rgba(122,143,190,.34)" },
          }}
        >
          {loading ? (
            <Box
              role="status"
              aria-label="Loading notifications"
              sx={{ minHeight: 104, display: "grid", placeItems: "center", py: 2 }}
            >
              <LoadingSpinner size={20} decorative />
            </Box>
          ) : !hasNotificationData && isError ? (
            <ErrorState
              title="Unable to load notifications"
              message={isError ? notificationQueryError : null}
              onRetry={isFetching ? undefined : () => refetch()}
              variant="container"
              sx={{
                minHeight: 132,
                py: 1.25,
                "& > .MuiPaper-root": {
                  p: 2,
                  borderColor: "#E5E7EB",
                  borderRadius: "14px",
                  boxShadow: "none",
                  "& .MuiStack-root > .MuiBox-root:first-of-type": {
                    width: 34,
                    height: 34,
                    bgcolor: "#F8FAFC",
                    color: "#64748B",
                  },
                  "& .MuiStack-root > .MuiBox-root:first-of-type svg": { fontSize: 20 },
                  "& h2": { fontSize: 15 },
                  "& p": { fontSize: 12.5, lineHeight: 1.45 },
                },
              }}
            />
          ) : !hasNotificationData ? (
            <ErrorState
              title="Notifications unavailable"
              message={user
                ? "Notification data is unavailable."
                : "Sign in to view notifications."}
              onRetry={user && !isFetching ? () => refetch() : undefined}
              variant="container"
              sx={{
                minHeight: 132,
                py: 1.25,
                "& > .MuiPaper-root": {
                  p: 2,
                  borderColor: "#E5E7EB",
                  borderRadius: "14px",
                  boxShadow: "none",
                  "& .MuiStack-root > .MuiBox-root:first-of-type": {
                    width: 34,
                    height: 34,
                    bgcolor: "#F8FAFC",
                    color: "#64748B",
                  },
                  "& .MuiStack-root > .MuiBox-root:first-of-type svg": { fontSize: 20 },
                  "& h2": { fontSize: 15 },
                  "& p": { fontSize: 12.5, lineHeight: 1.45 },
                },
              }}
            />
          ) : (
            <>
              {isError && (
                <ErrorState
                  title="Unable to refresh notifications"
                  message={notificationQueryError}
                  onRetry={isFetching ? undefined : () => refetch()}
                  variant="inline"
                  sx={{
                    px: 1.5,
                    py: 1.5,
                    "& > .MuiPaper-root": { p: 1.75, borderColor: "#E5E7EB", borderRadius: "14px", boxShadow: "none" },
                  }}
                />
              )}
              {!isError && notifications.length === 0 && (
                <EmptyState
                  icon={<NotificationsNoneOutlinedIcon />}
                  title="No new notifications"
                  description="You're all caught up."
                  sx={{
                    minHeight: 132,
                    py: 1.25,
                    "& > .MuiPaper-root": {
                      p: 2,
                      borderColor: "#E5E7EB",
                      borderRadius: "14px",
                      boxShadow: "none",
                      "& .MuiStack-root > .MuiBox-root:first-of-type": {
                        width: 34,
                        height: 34,
                        bgcolor: "#F8FAFC",
                        color: "#64748B",
                      },
                      "& .MuiStack-root > .MuiBox-root:first-of-type svg": { fontSize: 20 },
                      "& h2": { fontSize: 15 },
                      "& p": { fontSize: 12.5, lineHeight: 1.45 },
                    },
                  }}
                />
              )}
              {notifications.map((notification) => (
            <Box
              key={notification.id}
              component="button"
              type="button"
              onClick={() => openNotification(notification)}
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1,
                width: "100%",
                px: 1.5,
                py: 1.25,
                border: 0,
                borderBottom: "1px solid #E5E7EB",
                textAlign: "left",
                color: "#263754",
                background: "#FFFFFF",
                cursor: "pointer",
                font: "inherit",
                "&:hover": { background: "#F8FAFC" },
                "&:focus-visible": {
                  outline: "2px solid rgba(111,145,211,.48)",
                  outlineOffset: -2,
                  background: "#F8FAFC",
                },
              }}
            >
              <NotificationIcon type={notification.type} compact />
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography sx={{ fontSize: 14, lineHeight: 1.35, fontWeight: notification.is_read ? 500 : 600, color: "#172554", overflowWrap: "anywhere" }}>
                  {notification.title}
                </Typography>
                <Typography sx={{ mt: 0.3, fontSize: 12.5, lineHeight: 1.4, color: "#64748B", overflowWrap: "anywhere" }}>
                  {notification.organization_name}
                </Typography>
                <Typography sx={{ mt: 0.3, fontSize: 12.5, color: "#475569", lineHeight: 1.45, overflowWrap: "anywhere" }}>
                  {notification.post_title || notification.message}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 0.5, flexShrink: 0 }}>
                <Typography sx={{ fontSize: 11, color: "#8491A8", whiteSpace: "nowrap" }}>
                  {formatActivityDate(notification.created_at)}
                </Typography>
                {!notification.is_read && (
                  <Box
                    component="span"
                    role="img"
                    aria-label="Unread"
                    sx={{ width: 6, height: 6, borderRadius: "50%", bgcolor: "#8050EF" }}
                  />
                )}
              </Box>
            </Box>
              ))}
            </>
          )}
        </Box>
      </Popover>
    </>
  );
}
