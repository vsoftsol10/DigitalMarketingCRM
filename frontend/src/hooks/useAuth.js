import { useMutation } from "@tanstack/react-query";

import { useNavigate } from "react-router-dom";

import toast from "react-hot-toast";

import { authService } from "../services/auth.service";

import { useAuthContext } from "../context/AuthContext";

import { token } from "../utils/token";

export function useLogin() {
  const navigate = useNavigate();

  const { login } = useAuthContext();

  return useMutation({
    mutationFn: authService.login,

    onSuccess: (data) => {
      login(data);

      toast.success("Login successful");

      navigate("/");
    },

    onError: (error) => {
      const message = error.response?.data?.message || "Login failed";

      toast.error(message);
    },
  });
}

// export function useLogout() {
//   const navigate = useNavigate();
//   const { logout } = useAuthContext();

//   return useMutation({
//     mutationFn: async () => {
//       const refreshToken = token.getRefreshToken();
//       return authService.logout(refreshToken);
//     },

//     onSuccess: () => {
//       logout();
//       toast.success("Logged out successfully");
//       navigate("/login", { replace: true });
//     },

//     onError: () => {
//       logout();
//       navigate("/login", { replace: true });
//     },
//   });
// }

export function useLogout() {
  const navigate = useNavigate();

  const { logout } = useAuthContext();

  return useMutation({
    mutationFn: async () => {
      const refreshToken =
        token.getRefreshToken();

      // No refresh token means
      // user is already locally logged out.
      if (!refreshToken) {
        return null;
      }

      return authService.logout(
        refreshToken,
      );
    },

    onSuccess: () => {
      // Clear local authentication state
      logout();

      toast.success(
        "Logged out successfully",
      );

      navigate("/login", {
        replace: true,
      });
    },

    onError: () => {
      /*
       * Even if server logout fails,
       * local session must be destroyed.
       */
      logout();

      toast.success(
        "You have been logged out.",
      );

      navigate("/login", {
        replace: true,
      });
    },
  });
}
