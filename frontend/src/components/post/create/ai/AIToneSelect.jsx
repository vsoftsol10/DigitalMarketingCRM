// import FormSelect from "../../../ui/form/FormSelect";

// import { AI_TONE_OPTIONS } from "../../../../constants/ai/aiOptions";

// export default function AIToneSelect() {
//   return (
//     <FormSelect
//       name="ai_tone"
//       label="Tone"
//       options={AI_TONE_OPTIONS}
//       helperText="Choose the writing style for AI."
//     />
//   );
// }
import FormSelect from "../../../ui/form/FormSelect";

import { AI_TONE_OPTIONS } from "../../../../constants/ai/aiOptions";

export default function AIToneSelect() {
  return (
    <FormSelect
      name="ai_tone"
      label="Tone"
      options={AI_TONE_OPTIONS}
      helperText="Choose the writing style."
    />
  );
}