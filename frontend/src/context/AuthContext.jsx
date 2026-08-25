// import { createContext, useContext, useEffect, useState } from "react";

// import { token } from "../utils/token";
// import { authService } from "../services/auth.service";

// const AuthContext = createContext(null);

// export function AuthProvider({ children }) {
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true);

//   // const login = (data) => {
//   //   token.setTokens(data.access, data.refresh);
//   //   setUser(data.user);
//   // };
//   const login = (data) => {
//   console.log("LOGIN DATA:", data);
//   console.log("ACCESS TOKEN:", data?.access);
//   console.log("REFRESH TOKEN:", data?.refresh);

//   token.setTokens(
//     data.access,
//     data.refresh,
//   );

//   console.log(
//     "LOCAL ACCESS TOKEN:",
//     token.getAccessToken(),
//   );

//   console.log(
//     "LOCAL REFRESH TOKEN:",
//     token.getRefreshToken(),
//   );

//   setUser(data.user);
// };

//   const logout = () => {
//     token.clearTokens();
//     setUser(null);
//   };

//   useEffect(() => {
//     const restoreSession = async () => {
//       const accessToken = token.getAccessToken();

//       if (!accessToken) {
//         setLoading(false);
//         return;
//       }

//       try {
//         const user = await authService.getCurrentUser();
//         setUser(user);
//       } catch (error) {
//         console.log("Restore Session Catch");
//         debugger;
//         token.clearTokens();
//         setUser(null);
//       } finally {
//         setLoading(false);
//       }
//     };

//     restoreSession();
//   }, []);

//   return (
//     <AuthContext.Provider
//       value={{
//         user,
//         setUser,
//         login,
//         logout,
//         loading,
//         isAuthenticated: !!user,
//       }}
//     >
//       {children}
//     </AuthContext.Provider>
//   );
// }

// export function useAuthContext() {
//   return useContext(AuthContext);
// }


import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { token } from "../utils/token";
import { authService } from "../services/auth.service";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ==========================================
  // LOGIN
  // ==========================================

  const login = (data) => {
    token.setTokens(
      data.access,
      data.refresh,
    );

    setUser(data.user);
  };

  // ==========================================
  // LOGOUT
  // ==========================================

  const logout = () => {
    token.clearTokens();
    setUser(null);
  };

  // ==========================================
  // RESTORE SESSION
  // ==========================================

  useEffect(() => {
    const restoreSession = async () => {
      const accessToken =
        token.getAccessToken();

      if (!accessToken) {
        setLoading(false);
        return;
      }

      try {
        const currentUser =
          await authService.getCurrentUser();

        setUser(currentUser);
      } catch (error) {
        token.clearTokens();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        login,
        logout,
        loading,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  return useContext(AuthContext);
}