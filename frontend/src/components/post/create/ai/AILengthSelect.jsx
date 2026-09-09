// import FormSelect from "../../../ui/form/FormSelect";

// import { AI_LENGTH_OPTIONS } from "../../../../constants/ai/aiOptions";

// export default function AILengthSelect() {
//   return (
//     <FormSelect
//       name="ai_length"
//       label="Caption Length"
//       options={AI_LENGTH_OPTIONS}
//       helperText="Select the preferred caption length."
//     />
//   );
// }

import FormSelect from "../../../ui/form/FormSelect";

import { AI_LENGTH_OPTIONS } from "../../../../constants/ai/aiOptions";

export default function AILengthSelect() {
  return (
    <FormSelect
      name="ai_length"
      label="Caption Length"
      options={AI_LENGTH_OPTIONS}
      helperText="Choose the caption length."
    />
  );
}