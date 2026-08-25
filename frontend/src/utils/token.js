import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants/auth";
import { storage } from "./storage";

export const token = {
  getAccessToken() {
    return storage.get(ACCESS_TOKEN);
  },

  getRefreshToken() {
    return storage.get(REFRESH_TOKEN);
  },

  setTokens(access, refresh) {
    storage.set(ACCESS_TOKEN, access);
    storage.set(REFRESH_TOKEN, refresh);
  },

  setAccessToken(access) {
    storage.set(ACCESS_TOKEN, access);
  },

  setRefreshToken(refresh) {
    storage.set(REFRESH_TOKEN, refresh);
  },

  clearTokens() {
    storage.remove(ACCESS_TOKEN);
    storage.remove(REFRESH_TOKEN);
  },
};