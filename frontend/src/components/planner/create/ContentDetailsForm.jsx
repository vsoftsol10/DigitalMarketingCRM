// import { Grid } from "@mui/material";

// import FormSection from "../../ui/form/FormSection";
// import FormSelect from "../../ui/form/FormSelect";
// import FormTextArea from "../../ui/form/FormTextArea";

// import { CONTENT_TYPE_OPTIONS } from "../../../constants/form-options/contentTypeOptions";
// import { CAMPAIGN_GOAL_OPTIONS } from "../../../constants/form-options/campaignGoalOptions";

// export default function ContentDetailsForm() {
//   return (
//     <FormSection
//       title="Content Details"
//       description="Describe the content idea and its objective."
//     >
//       <Grid container spacing={3}>
//         {/* Content Type */}

//         <Grid size={{ xs: 12, md: 6 }}>
//           <FormSelect
//             name="content_type"
//             label="Content Type"
//             required
//             placeholder="Select Content Type"
//             options={CONTENT_TYPE_OPTIONS}
//           />
//         </Grid>

//         {/* Campaign Goal */}

//         <Grid size={{ xs: 12, md: 6 }}>
//           <FormSelect
//             name="campaign_goal"
//             label="Campaign Goal"
//             required
//             placeholder="Select Campaign Goal"
//             options={CAMPAIGN_GOAL_OPTIONS}
//           />
//         </Grid>

//         {/* Description */}

//         <Grid size={{ xs: 12 }}>
//           <FormTextArea
//             name="description"
//             label="Description"
//             rows={5}
//             placeholder="Describe your content idea..."
//           />
//         </Grid>
//       </Grid>
//     </FormSection>
//   );
// }
import { useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";

import { Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import FormSelect from "../../ui/form/FormSelect";
import FormTextArea from "../../ui/form/FormTextArea";

import { getContentTypeOptions } from "../../../constants/form-options/contentTypeOptions";

import { CAMPAIGN_GOAL_OPTIONS } from "../../../constants/form-options/campaignGoalOptions";

export default function ContentDetailsForm() {
  const { control, setValue } = useFormContext();

  const platform = useWatch({
    control,
    name: "platform",
  });

  const contentType = useWatch({
    control,
    name: "content_type",
  });

  const contentTypeOptions = getContentTypeOptions(platform);

  useEffect(() => {
    if (!platform) {
      if (contentType) {
        setValue("content_type", "", {
          shouldValidate: true,
          shouldDirty: true,
        });
      }

      return;
    }

    const isCurrentContentTypeValid = contentTypeOptions.some(
      (option) => option.value === contentType,
    );

    if (contentType && !isCurrentContentTypeValid) {
      setValue("content_type", "", {
        shouldValidate: true,
        shouldDirty: true,
      });
    }
  }, [platform, contentType, contentTypeOptions, setValue]);

  return (
    <FormSection
      title="Content Details"
      description="Describe the content idea and its objective."
    >
      <Grid container spacing={3}>
        {/* ===================================================
            CONTENT TYPE
        =================================================== */}

        <Grid size={{ xs: 12, md: 6 }}>
          <FormSelect
            name="content_type"
            label="Content Type"
            required
            placeholder={
              platform ? "Select Content Type" : "Select Platform First"
            }
            options={contentTypeOptions}
            disabled={!platform}
          />
        </Grid>

        {/* ===================================================
            CAMPAIGN GOAL
        =================================================== */}

        <Grid size={{ xs: 12, md: 6 }}>
          <FormSelect
            name="campaign_goal"
            label="Campaign Goal"
            required
            placeholder="Select Campaign Goal"
            options={CAMPAIGN_GOAL_OPTIONS}
          />
        </Grid>

        {/* ===================================================
            DESCRIPTION
        =================================================== */}

        <Grid size={{ xs: 12 }}>
          <FormTextArea
            name="description"
            label="Description"
            rows={5}
            placeholder="Describe your content idea..."
          />
        </Grid>
      </Grid>
    </FormSection>
  );
}
