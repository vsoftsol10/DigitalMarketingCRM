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
import { Grid } from "@mui/material";

import FormSection from "../../ui/form/FormSection";
import FormSelect from "../../ui/form/FormSelect";
import FormTextArea from "../../ui/form/FormTextArea";

import FormTextField from "../../ui/form/FormTextField";

const CONTENT_TYPE_OPTIONS = [
  { value: "POST", label: "Post" },
  { value: "REEL", label: "Reel" },
  { value: "STORY", label: "Story" },
];

export default function ContentDetailsForm() {
  return (
    <FormSection
      title="Content Details"
      description="Describe the content idea and its objective."
    >
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <FormSelect
            name="content_type"
            label="Content Type"
            required
            placeholder="Select Content Type"
            options={CONTENT_TYPE_OPTIONS}
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="target_publish_date"
            label="Target Publish Date"
            required
            type="date"
            InputLabelProps={{ shrink: true }}
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <FormTextField
            name="target_publish_time"
            label="Target Publish Time"
            required
            type="time"
            InputLabelProps={{ shrink: true }}
          />
        </Grid>

        <Grid size={{ xs: 12 }}>
          <FormTextArea
            name="caption"
            label="Caption"
            required
            rows={4}
            placeholder="Write the post caption..."
          />
        </Grid>

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
