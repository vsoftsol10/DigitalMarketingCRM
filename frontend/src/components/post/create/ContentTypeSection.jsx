import { Alert, Stack, Typography } from "@mui/material";

import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

import { useFormContext } from "react-hook-form";

import toast from "react-hot-toast";

import SectionCard from "./SectionCard";
import PlatformContentTypeRow from "./PlatformContentTypeRow";

import { getPlatformStates } from "../../../utils/post/platformCapability.utils";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function ContentTypeSection({ platforms = [] }) {
  const {
    watch,
    setValue,
    formState: { errors },
  } = useFormContext();

  // ============================================================
  // FORM STATE
  // ============================================================

  const selectedPlatforms = watch("platforms") || [];

  const media = watch("media") || [];

  const platformContentTypes = watch("platform_content_types") || {};

  // ============================================================
  // CAPABILITY STATES
  // ============================================================

  const platformStates = getPlatformStates({
    media,
  });

  // ============================================================
  // CAPABILITY LOOKUP
  // ============================================================

  const capabilityMap = new Map(
    platformStates.map((item) => [item.platform, item]),
  );

  // ============================================================
  // SELECTED PLATFORM DEFINITIONS
  // ============================================================

  const selectedPlatformDefinitions = platforms.filter((platform) =>
    selectedPlatforms.includes(platform.id),
  );

  // ============================================================
  // CONTENT TYPE CHANGE
  // ============================================================

  function handleContentTypeChange(platformId, contentType) {
    const platformState = capabilityMap.get(platformId);

    const option = platformState?.contentTypes?.find(
      (item) => item.value === contentType,
    );

    // ----------------------------------------------------------
    // INVALID OPTION
    // ----------------------------------------------------------

    if (!option || !option.available) {
      toast.error(
        option?.reason ||
          "This content type is not compatible with the selected media.",
      );

      return;
    }

    // ----------------------------------------------------------
    // VALID OPTION
    // ----------------------------------------------------------

    setValue(`platform_content_types.${platformId}`, contentType, {
      shouldDirty: true,
      shouldValidate: true,
    });
  }

  // ============================================================
  // NO PLATFORM
  // ============================================================

  if (selectedPlatformDefinitions.length === 0) {
    return null;
  }

  // ============================================================
  // MEDIA NOT UPLOADED
  // ============================================================

  if (!media.length) {
    return (
      <SectionCard
        title="Content Type"
        description="Choose the publishing format for each selected platform."
      >
        <Alert
          severity="info"
          icon={<InfoOutlinedIcon />}
          sx={{
            borderRadius: 2,
            fontSize: 13,
          }}
        >
          Upload media first to see the content types available for each
          selected platform.
        </Alert>
      </SectionCard>
    );
  }

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <SectionCard
      title="Content Type"
      description="Choose the publishing format for each selected platform."
    >
      <Stack spacing={2.5}>
        {selectedPlatformDefinitions.map((platform) => {
          const platformState = capabilityMap.get(platform.id);

          const contentTypes = platformState?.contentTypes || [];

          const value = platformContentTypes[platform.id] || "";

          const currentOption = contentTypes.find(
            (item) => item.value === value,
          );

          // ==================================================
          // RHF / ZOD ERROR
          // ==================================================

          const fieldError = errors?.platform_content_types?.[platform.id];

          // ==================================================
          // INVALID CURRENT VALUE
          // ==================================================

          const capabilityError = Boolean(
            value && (!currentOption || !currentOption.available),
          );

          // ==================================================
          // FINAL ERROR STATE
          // ==================================================

          const hasError = Boolean(fieldError || capabilityError);

          // ==================================================
          // ERROR MESSAGE
          // ==================================================

          const errorMessage =
            fieldError?.message ||
            currentOption?.reason ||
            platformState?.reason ||
            "Please select a valid content type.";

          // ==================================================
          // AVAILABLE TYPES
          // ==================================================

          const hasAvailableType = contentTypes.some((item) => item.available);

          return (
            <PlatformContentTypeRow
              key={platform.id}
              platform={platform}
              contentTypes={contentTypes}
              value={value}
              onChange={(nextContentType) =>
                handleContentTypeChange(platform.id, nextContentType)
              }
              invalidSelection={hasError}
              invalidReason={errorMessage}
              noAvailableType={!hasAvailableType}
            />
          );
        })}

        {/* ======================================================
            HELPER
        ====================================================== */}

        <Typography
          sx={{
            ...TYPOGRAPHY.helperText,
            color: "text.secondary",
            pt: 0.25,
          }}
        >
          Available content types are determined automatically from the selected
          media and each platform's capabilities.
        </Typography>
      </Stack>
    </SectionCard>
  );
}
