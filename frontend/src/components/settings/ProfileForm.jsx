import {
  Alert,
  Avatar,
  Box,
  Button,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import PhotoCameraOutlinedIcon from "@mui/icons-material/PhotoCameraOutlined";

import { useEffect, useRef, useState } from "react";

import {
  Controller,
  useForm,
} from "react-hook-form";

import { TYPOGRAPHY } from "../../theme/typography";

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
          mt: 2.75,
        }}
      >
        {/* Avatar */}

        <Avatar
          src={imagePreview || undefined}
          alt={
            profile?.fullName ||
            "Profile"
          }
          sx={{
            width: {
              xs: 72,
              sm: 100,
            },

            height: {
              xs: 72,
              sm: 100,
            },

            flexShrink: 0,

            bgcolor: "primary.main",

            color: "primary.contrastText",

            fontSize: {
              xs: 24,
              sm: 28,
            },

            fontWeight: 700,
          }}
        >
          {!imagePreview && profileInitial}
        </Avatar>

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

              border: "none",

              p: 0,

              bgcolor: "transparent",

              color: "primary.main",

              cursor: loading
                ? "default"
                : "pointer",

              ...TYPOGRAPHY.bodySmall,

              fontWeight: 600,

              "&:hover": {
                textDecoration: loading
                  ? "none"
                  : "underline",
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

      <Divider
        sx={{
          my: 3,
        }}
      />

      {/* =====================================
          DETAILS
      ===================================== */}

      <Typography
        component="h3"
        sx={{
          ...TYPOGRAPHY.cardTitle,

          color: "text.primary",

          fontWeight: 700,

          mb: 2,
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
              borderRadius: 2,
            }}
          >
            {error}
          </Alert>
        )}

      {/* =====================================
          NAME
      ===================================== */}

      <Controller
        name="name"
        control={control}
        rules={{
          required: "Name is required.",
          validate: (value) =>
            value?.trim()
              ? true
              : "Name is required.",
        }}
        render={({
          field,
          fieldState,
        }) => (
          <TextField
            {...field}
            fullWidth
            label="Name"
            required
            error={
              !!fieldState.error ||
              !!firstNameError
            }
            helperText={
              fieldState.error?.message ||
              firstNameError
            }
            disabled={loading}
            size="small"
          />
        )}
      />

      {/* =====================================
          EMAIL
      ===================================== */}

      <Box
        sx={{
          mt: 2,
        }}
      >
        <TextField
          fullWidth
          label="Email"
          value={profile?.email || ""}
          disabled
          helperText="Email address cannot be changed from settings."
          size="small"
        />
      </Box>

      {/* =====================================
          PHONE
      ===================================== */}

      <Box
        sx={{
          mt: 2,
          maxWidth: {
            xs: "100%",
            sm: 444,
          },
        }}
      >
        <Controller
          name="phone"
          control={control}
          render={({
            field,
            fieldState,
          }) => (
            <TextField
              {...field}
              fullWidth
              label="Phone number"
              error={
                !!fieldState.error ||
                !!getFieldError("phone")
              }
              helperText={
                fieldState.error?.message ||
                getFieldError("phone")
              }
              disabled={loading}
              size="small"
            />
          )}
        />
      </Box>

      {/* =====================================
          INFORMATION MESSAGE
      ===================================== */}

      <Box
        sx={{
          mt: 3,

          px: 1.5,
          py: 1.25,

          display: "flex",

          alignItems: "center",

          gap: 1,

          borderRadius: 2,

          bgcolor: "action.hover",

          color: "text.secondary",
        }}
      >
        <ShieldOutlinedIcon
          sx={{
            fontSize: 18,

            color: "text.secondary",

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

      {/* =====================================
          ACTION
      ===================================== */}

      <Box
        sx={{
          mt: 2.5,

          pt: 2,

          borderTop: "1px solid",

          borderColor: "divider",

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
            minWidth: 130,

            height: 44,

            px: 2.5,

            borderRadius: 2,

            ...TYPOGRAPHY.button,

            fontWeight: 600,
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