// import { Box, CircularProgress, Typography } from "@mui/material";

// import SettingsHeader from "../../components/settings/SettingsHeader";
// import ProfileSettings from "../../components/settings/ProfileSettings";
// import SecuritySettings from "../../components/settings/SecuritySettings";

// import useSettings from "../../hooks/settings/useSettings";
// import SignOutSettings from "../../components/settings/SignOutSettings";
// import { useAuthContext } from "../../context/AuthContext";
// export default function Settings() {
//   const { logout } = useAuthContext();
//   const {
//     profile,

//     profileLoading,
//     profileError,

//     profileUpdating,
//     profileUpdateError,

//     passwordChanging,
//     passwordError,

//     updateProfile,
//     changePassword,
//   } = useSettings();

//   // ==========================================
//   // LOADING
//   // ==========================================

//   if (profileLoading) {
//     return (
//       <Box
//         sx={{
//           width: "100%",
//           minHeight: 400,

//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",
//         }}
//       >
//         <CircularProgress size={28} />
//       </Box>
//     );
//   }

//   // ==========================================
//   // ERROR
//   // ==========================================

//   if (profileError) {
//     return (
//       <Box
//         sx={{
//           width: "100%",
//           minHeight: 400,

//           display: "flex",
//           flexDirection: "column",

//           alignItems: "center",
//           justifyContent: "center",

//           gap: 1,
//         }}
//       >
//         <Typography
//           sx={{
//             fontWeight: 600,
//             color: "text.primary",
//           }}
//         >
//           Unable to load settings
//         </Typography>

//         <Typography
//           sx={{
//             color: "text.secondary",
//           }}
//         >
//           {profileError}
//         </Typography>
//       </Box>
//     );
//   }

//   return (
//     <Box
//       sx={{
//         width: "100%",
//         minWidth: 0,

//         boxSizing: "border-box",

//         pb: 6,
//       }}
//     >
//       {/* ======================================
//           PAGE HEADER
//       ====================================== */}

//       <SettingsHeader />

//       {/* ======================================
//           SETTINGS CONTENT
//       ====================================== */}

//       <Box
//         sx={{
//           width: "100%",

//           maxWidth: 840,

//           mx: "auto",

//           mt: {
//             xs: 3,
//             sm: 4,
//           },

//           display: "flex",

//           flexDirection: "column",

//           gap: 3,
//         }}
//       >
//         {/* ====================================
//             PROFILE
//         ==================================== */}

//         <ProfileSettings
//           profile={profile}
//           loading={profileUpdating}
//           error={profileUpdateError}
//           onSubmit={updateProfile}
//         />

//         {/* ====================================
//             SECURITY
//         ==================================== */}

//         <SecuritySettings
//           loading={passwordChanging}
//           error={passwordError}
//           onSubmit={changePassword}
//         />

//         <SignOutSettings onLogout={logout} />
//       </Box>
//     </Box>
//   );
// }


import {
  Box,
} from "@mui/material";

import SettingsHeader from "../../components/settings/SettingsHeader";
import ProfileSettings from "../../components/settings/ProfileSettings";
import SecuritySettings from "../../components/settings/SecuritySettings";
import SignOutSettings from "../../components/settings/SignOutSettings";

import useSettings from "../../hooks/settings/useSettings";
import { useLogout } from "../../hooks/useAuth";
import LoadingState from "../../components/ui/LoadingState";
import ErrorState from "../../components/ui/ErrorState";
import { settingsGlassCardSx, settingsPrimaryButtonSx } from "../../components/settings/settingsGlassSx";

export default function Settings() {
  // ==========================================
  // LOGOUT
  // ==========================================

  const logoutMutation = useLogout();

  // ==========================================
  // SETTINGS
  // ==========================================

  const {
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
  } = useSettings();

  // ==========================================
  // PROFILE LOADING
  // ==========================================

  if (profileLoading) {
    return <LoadingState page="Settings" sx={{ "& p": { color: "#667792" } }} />;
  }

  // ==========================================
  // PROFILE ERROR
  // ==========================================

  if (profileError) {
    return (
      <ErrorState
        title="Unable to load settings"
        message={profileError}
        onRetry={refresh}
        variant="page"
        sx={{
          "& > .MuiPaper-root": settingsGlassCardSx,
          "& .MuiButton-contained": settingsPrimaryButtonSx,
        }}
      />
    );
  }

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <Box
      sx={{
        width: "100%",
        minWidth: 0,

        boxSizing: "border-box",

        pb: 6,
      }}
    >
      {/* ======================================
          PAGE HEADER
      ====================================== */}

      <SettingsHeader />

      {/* ======================================
          SETTINGS CONTENT
      ====================================== */}

      <Box
        sx={{
          width: "100%",
          minWidth: 0,

          maxWidth: 960,

          mx: "auto",

          mt: {
            xs: 3,
            sm: 3,
          },

          display: "flex",

          flexDirection: "column",

          gap: { xs: 2, sm: 3 },
        }}
      >
        {/* ====================================
            PROFILE
        ==================================== */}

        <ProfileSettings
          profile={profile}
          loading={profileUpdating}
          error={profileUpdateError}
          onSubmit={updateProfile}
        />

        {/* ====================================
            SECURITY
        ==================================== */}

        <SecuritySettings
          loading={passwordChanging}
          error={passwordError}
          onSubmit={changePassword}
        />

        {/* ====================================
            SIGN OUT
        ==================================== */}

        <SignOutSettings
          onLogout={logoutMutation.mutate}
          loading={logoutMutation.isPending}
        />
      </Box>
    </Box>
  );
}
