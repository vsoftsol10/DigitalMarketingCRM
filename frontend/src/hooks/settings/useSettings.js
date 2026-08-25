import { useCallback, useEffect, useState } from "react";

import settingsService from "../../services/settings.service";
import toast from "react-hot-toast";

export default function useSettings() {
  // ==========================================
  // PROFILE
  // ==========================================

  const [profile, setProfile] = useState(null);

  // ==========================================
  // PROFILE LOADING
  // ==========================================

  const [profileLoading, setProfileLoading] = useState(true);

  // ==========================================
  // PROFILE ERROR
  // ==========================================

  const [profileError, setProfileError] = useState(null);

  // ==========================================
  // PROFILE UPDATE
  // ==========================================

  const [profileUpdating, setProfileUpdating] = useState(false);

  const [profileUpdateError, setProfileUpdateError] = useState(null);

  // ==========================================
  // PASSWORD CHANGE
  // ==========================================

  const [passwordChanging, setPasswordChanging] = useState(false);

  const [passwordError, setPasswordError] = useState(null);

  // ==========================================
  // FETCH PROFILE
  // ==========================================

  const fetchProfile = useCallback(async () => {
    setProfileLoading(true);
    setProfileError(null);

    try {
      const data = await settingsService.getProfile();

      setProfile(data);
    } catch (error) {
      console.error("Failed to fetch settings profile:", error);

      setProfile(null);

      setProfileError(
        error?.response?.data?.message ||
          error?.response?.data?.detail ||
          error?.message ||
          "Unable to load profile.",
      );
    } finally {
      setProfileLoading(false);
    }
  }, []);

  // ==========================================
  // INITIAL LOAD
  // ==========================================

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // ==========================================
  // UPDATE PROFILE
  // ==========================================

  const updateProfile = useCallback(async (data) => {
    setProfileUpdating(true);
    setProfileUpdateError(null);

    try {
      const updatedProfile = await settingsService.updateProfile(data);

      setProfile(updatedProfile);

      return {
        success: true,
        data: updatedProfile,
      };
    } catch (error) {
      console.error("Failed to update profile:", error);

      const errorMessage =
        error?.response?.data?.errors ||
        error?.response?.data?.message ||
        error?.message ||
        "Unable to update profile.";

      setProfileUpdateError(errorMessage);

      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      setProfileUpdating(false);
    }
  }, []);

  // ==========================================
  // CHANGE PASSWORD
  // ==========================================

  // const changePassword = useCallback(
  //   async (data) => {
  //     setPasswordChanging(true);
  //     setPasswordError(null);

  //     try {
  //       const response =
  //         await settingsService.changePassword(
  //           data,
  //         );

  //       return {
  //         success: true,
  //         data: response,
  //       };
  //     } catch (error) {
  //       console.error(
  //         "Failed to change password:",
  //         error,
  //       );

  //       const errorData =
  //         error?.response?.data;

  //       const errorMessage =
  //         errorData?.errors ||
  //         errorData?.message ||
  //         error?.message ||
  //         "Unable to change password.";

  //       setPasswordError(
  //         errorMessage,
  //       );

  //       return {
  //         success: false,
  //         error: errorMessage,
  //       };
  //     } finally {
  //       setPasswordChanging(false);
  //     }
  //   },
  //   [],
  // );
  const changePassword = useCallback(async (data) => {
    setPasswordChanging(true);
    setPasswordError(null);

    try {
      const response = await settingsService.changePassword(data);

      toast.success("Password updated successfully.");

      return {
        success: true,
        data: response,
      };
    } catch (error) {
      console.error("Failed to change password:", error);

      const errorData = error?.response?.data;

      const errorMessage =
        errorData?.errors ||
        errorData?.message ||
        error?.message ||
        "Unable to change password.";

      setPasswordError(errorMessage);

      return {
        success: false,
        error: errorMessage,
      };
    } finally {
      setPasswordChanging(false);
    }
  }, []);

  // ==========================================
  // REFRESH
  // ==========================================

  const refresh = useCallback(() => {
    return fetchProfile();
  }, [fetchProfile]);

  // ==========================================
  // RETURN
  // ==========================================

  return {
    profile,

    profileLoading,
    profileError,

    profileUpdating,
    profileUpdateError,

    passwordChanging,
    passwordError,

    updateProfile,
    changePassword,

    refresh,
  };
}
