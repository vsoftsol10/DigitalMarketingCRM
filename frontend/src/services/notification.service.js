import api from "../api/axios";

export const NOTIFICATION_QUERY_KEY = ["header-notifications"];

const notificationService = {
  async getNotifications() {
    const response = await api.get("/notifications/");
    return response.data?.data;
  },

  async markAsRead(notificationId) {
    const response = await api.post(`/notifications/${notificationId}/read/`);
    return response.data?.data;
  },
};

export default notificationService;
