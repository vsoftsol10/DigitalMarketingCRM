import {
  Alert,
  Avatar,
  Box,
  Button,
  Divider,
  Grid,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import PhotoCameraOutlinedIcon from "@mui/icons-material/PhotoCameraOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import MailOutlineOutlinedIcon from "@mui/icons-material/MailOutlineOutlined";
import PhoneOutlinedIcon from "@mui/icons-material/PhoneOutlined";

import { useEffect, useRef, useState } from "react";

import {
  Controller,
  useForm,
} from "react-hook-form";

import { TYPOGRAPHY } from "../../theme/typography";
import {
  settingsFieldSx,
  settingsErrorAlertSx,
  settingsPrimaryButtonSx,
  settingsSecondaryButtonSx,
} from "./settingsGlassSx";

const DEFAULT_VALUES = {
  name: "",
  phone: "",
};

export default function ProfileForm({
  profile,
  loading = false,
  error = null,
  onSubmit,
}) {
  const {
    control,
    handleSubmit,
    reset,
  } = useForm({
    defaultValues: DEFAULT_VALUES,
    mode: "onSubmit",
  });

  const fileInputRef = useRef(null);

  const [selectedImage, setSelectedImage] =
    useState(null);

  const [imagePreview, setImagePreview] =
    useState(null);

  // ==========================================
  // LOAD PROFILE
  // ==========================================

  useEffect(() => {
    if (!profile) {
      return;
    }

    reset({
      name: profile.fullName || "",
      phone: profile.phone || "",
    });

    // This effect syncs the image preview with the loaded profile record.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setImagePreview(
      profile.profileImage || null,
    );

    setSelectedImage(null);
  }, [profile, reset]);

  // ==========================================
  // CLEANUP IMAGE PREVIEW
  // ==========================================

  useEffect(() => {
    return () => {
      if (
        imagePreview &&
        imagePreview.startsWith("blob:")
      ) {
        URL.revokeObjectURL(imagePreview);
      }
    };
  }, [imagePreview]);

  // ==========================================
  // PROFILE INITIAL
  // ==========================================

  const profileInitial =
    profile?.firstName
      ?.charAt(0)
      ?.toUpperCase() ||
    profile?.fullName
      ?.charAt(0)
      ?.toUpperCase() ||
    "U";

  // ==========================================
  // IMAGE SELECT
  // ==========================================

  function handleImageSelect(event) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    // ----------------------------------------
    // Basic frontend validation
    // ----------------------------------------

    if (!file.type.startsWith("image/")) {
      event.target.value = "";
      return;
    }

    const MAX_FILE_SIZE = 5 * 1024 * 1024;

    if (file.size > MAX_FILE_SIZE) {
      event.target.value = "";
      return;
    }

    // ----------------------------------------
    // Revoke previous blob preview
    // ----------------------------------------

    if (
      imagePreview &&
      imagePreview.startsWith("blob:")
    ) {
      URL.revokeObjectURL(imagePreview);
    }

    const previewUrl =
      URL.createObjectURL(file);

    setSelectedImage(file);
    setImagePreview(previewUrl);

    // Allow selecting the same file again
    event.target.value = "";
  }

  // ==========================================
  // OPEN FILE PICKER
  // ==========================================

  function handleChangeProfileImage() {
    fileInputRef.current?.click();
  }

  // ==========================================
  // SUBMIT
  // ==========================================

  async function handleFormSubmit(data) {
    const trimmedName =
      data.name?.trim() || "";

    const nameParts =
      trimmedName.split(/\s+/);

    const firstName =
      nameParts.shift() || "";

    const lastName =
      nameParts.join(" ");

    const payload = {
      first_name: firstName,
      last_name: lastName,
      phone: data.phone?.trim() || "",
    };

    if (selectedImage) {
      payload.profile_image = selectedImage;
    }

    await onSubmit?.(payload);
  }

  // ==========================================
  // FIELD ERROR
  // ==========================================

  function getFieldError(field) {
    if (!error || typeof error !== "object") {
      return undefined;
    }

    const value = error[field];

    if (Array.isArray(value)) {
      return value[0];
    }

    return value;
  }

  const firstNameError =
    getFieldError("first_name");

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <Box
      component="form"
      onSubmit={handleSubmit(handleFormSubmit)}
      noValidate
    >
      {/* =====================================
          PROFILE INFORMATION
      ===================================== */}

      <Box>
        <Typography
          component="h2"
          sx={{
            ...TYPOGRAPHY.cardTitle,

            color: "text.primary",

            fontSize: {
              xs: "20px",
              sm: "22px",
            },

            lineHeight: {
              xs: "28px",
              sm: "30px",
            },

            fontWeight: 700,
          }}
        >
          Profile Information
        </Typography>

        <Typography
          component="p"
          sx={{
            ...TYPOGRAPHY.body,

            mt: 0.35,

            color: "text.secondary",
          }}
        >
          Your name, photo, and contact details
        </Typography>
      </Box>

      {/* =====================================
          PROFILE SUMMARY
      ===================================== */}

      <Stack
        direction="row"
        alignItems="center"
        spacing={2.5}
        sx={{
          mt: 2.25,
          flexWrap: "wrap",
        }}
      >
        {/* Avatar */}
        <Box
          sx={{
            position: "relative",
            width: { xs: 76, sm: 100 },
            height: { xs: 76, sm: 100 },
            flexShrink: 0,
          }}
        >
          <Avatar
            src={imagePreview || undefined}
            alt={profile?.fullName || "Profile"}
            sx={{
              width: "100%",
              height: "100%",
              border: "3px solid #FFFFFF",
              boxShadow: "0 5px 12px rgba(41,55,103,.12)",
              background: "linear-gradient(110deg, #8B4BF5, #3977F6)",
              color: "#FFFFFF",
              fontSize: { xs: 24, sm: 28 },
              fontWeight: 700,
            }}
          >
            {!imagePreview && profileInitial}
          </Avatar>
          <IconButton
            type="button"
            aria-label="Change profile image"
            onClick={handleChangeProfileImage}
            disabled={loading}
            size="small"
            sx={{
              position: "absolute",
              right: -3,
              bottom: -2,
              width: 34,
              height: 34,
              border: "2px solid #FFFFFF",
              borderRadius: "50%",
              color: "#FFFFFF",
              background: "linear-gradient(110deg, #8B4BF5, #3977F6)",
              boxShadow: "0 3px 8px rgba(83,75,196,.18)",
              "&:hover": { background: "linear-gradient(110deg, #7D3CEB, #2F6EEA)" },
            }}
          >
            <PhotoCameraOutlinedIcon sx={{ fontSize: 17 }} />
          </IconButton>
        </Box>

        {/* Profile details */}

        <Box
          sx={{
            minWidth: 0,
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.cardTitle,

              color: "text.primary",

              fontWeight: 700,

              wordBreak: "break-word",
            }}
          >
            {profile?.fullName ||
              "Your profile"}
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,

              mt: 0.25,

              color: "text.secondary",

              wordBreak: "break-word",
            }}
          >
            Agency Admin
          </Typography>

          <Box
            component="button"
            type="button"
            onClick={
              handleChangeProfileImage
            }
            disabled={loading}
            sx={{
              mt: 1,

              display: "inline-flex",

              alignItems: "center",

              gap: 0.75,

              ...settingsSecondaryButtonSx,
              minHeight: 38,
              px: 1.5,
              py: 0.5,
              color: "#6941D9",

              cursor: loading
                ? "default"
                : "pointer",

              ...TYPOGRAPHY.bodySmall,

              fontWeight: 600,

              "&:hover": {
                textDecoration: "none",
                background: "#F5F2FF",
                borderColor: "#C8BDF5",
                cursor: loading ? "default" : "pointer",
              },
            }}
          >
            <PhotoCameraOutlinedIcon
              sx={{
                fontSize: 18,
              }}
            />

            Change profile image
          </Box>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={handleImageSelect}
          />
        </Box>
      </Stack>

      {/* =====================================
          DIVIDER
      ===================================== */}

      <Divider sx={{ my: 2.25, borderColor: "#E5E9F1" }} />

      {/* =====================================
          DETAILS
      ===================================== */}

      <Box
        sx={{
          p: 0,
        }}
      >
      <Typography
        component="h3"
        sx={{
          ...TYPOGRAPHY.cardTitle,
          color: "#12264D",
          fontWeight: 700,
          mb: 1.75,
        }}
      >
        Details
      </Typography>

      {/* =====================================
          API ERROR
      ===================================== */}

      {error &&
        typeof error === "string" && (
          <Alert
            severity="error"
            sx={{
              mb: 2.5,
              ...settingsErrorAlertSx,
            }}
          >
            {error}
          </Alert>
        )}

      {/* =====================================
          NAME
      ===================================== */}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="name"
            control={control}
            rules={{
              required: "Name is required.",
              validate: (value) => value?.trim() ? true : "Name is required.",
            }}
            render={({ field, fieldState }) => (
              <TextField
                {...field}
                fullWidth
                label="Name"
                required
                error={!!fieldState.error || !!firstNameError}
                helperText={fieldState.error?.message || firstNameError}
                disabled={loading}
                size="small"
                sx={settingsFieldSx}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonOutlineOutlinedIcon sx={{ color: "#7D91B8", fontSize: 20 }} />
                      </InputAdornment>
                    ),
                  },
                }}
              />
            )}
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <TextField
            fullWidth
            label="Email"
            value={profile?.email || ""}
            disabled
            helperText="Email address cannot be changed from settings."
            size="small"
            sx={settingsFieldSx}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <MailOutlineOutlinedIcon sx={{ color: "#7D91B8", fontSize: 20 }} />
                  </InputAdornment>
                ),
              },
            }}
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="phone"
            control={control}
            render={({ field, fieldState }) => (
              <TextField
                {...field}
                fullWidth
                label="Phone number"
                error={!!fieldState.error || !!getFieldError("phone")}
                helperText={fieldState.error?.message || getFieldError("phone")}
                disabled={loading}
                size="small"
                sx={settingsFieldSx}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <PhoneOutlinedIcon sx={{ color: "#7D91B8", fontSize: 20 }} />
                      </InputAdornment>
                    ),
                  },
                }}
              />
            )}
          />
        </Grid>
      </Grid>

      {/* =====================================
          INFORMATION MESSAGE
      ===================================== */}

      <Box
        sx={{
          mt: 2.25,

          px: 1.5,
          py: 1.25,

          display: "flex",

          alignItems: "center",

          gap: 1,

          borderRadius: "14px",
          border: "1px solid #E5E9F1",
          background: "#F8FAFC",
          color: "#667792",
        }}
      >
        <ShieldOutlinedIcon
          sx={{
            fontSize: 18,

            color: "#71809A",

            flexShrink: 0,
          }}
        />

        <Typography
          sx={{
            ...TYPOGRAPHY.caption,

            color: "text.secondary",
          }}
        >
          Your profile information is used
          across the CRM and on exported
          reports.
        </Typography>
      </Box>
      </Box>

      {/* =====================================
          ACTION
      ===================================== */}

      <Box
        sx={{
          mt: 2.5,

          pt: 2,

          borderTop: "1px solid",

          borderColor: "#E5E9F1",

          display: "flex",

          justifyContent: "flex-end",
        }}
      >
        <Button
          type="submit"
          variant="contained"
          disableElevation
          disabled={loading}
          sx={{
            minWidth: 144,

            height: 46,

            px: 2.5,

            ...TYPOGRAPHY.button,
            fontWeight: 600,
            ...settingsPrimaryButtonSx,
          }}
        >
          {loading
            ? "Saving..."
            : "Save changes"}
        </Button>
      </Box>
    </Box>
  );
}
