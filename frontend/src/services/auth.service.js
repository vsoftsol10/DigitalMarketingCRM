import api from "../api/axios";
import { API_ENDPOINTS } from "../api/endpoints";

export const authService = {
  async login(data) {
    const response = await api.post(
      API_ENDPOINTS.AUTH.LOGIN,
      data
    );

    return response.data.data;
  },

  async getCurrentUser() {
    const response = await api.get(
      API_ENDPOINTS.AUTH.ME
    );

    return response.data.data;
  },

  async logout(refresh) {
    const response = await api.post(
      API_ENDPOINTS.AUTH.LOGOUT,
      {
        refresh,
      }
    );

    return response.data.data;
  },

  async refreshToken(refresh) {
    const response = await api.post(
      API_ENDPOINTS.AUTH.REFRESH,
      {
        refresh,
      }
    );

    return response.data;
  },
};