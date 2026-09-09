// import FormTextArea from "../../../ui/form/FormTextArea";

// export default function AIPromptField() {
//   return (
//     <FormTextArea
//       name="ai_prompt"
//       label="Describe your post"
//       rows={4}
//       placeholder="Example: Launching our new cold brew coffee this weekend. Write an engaging Instagram caption highlighting freshness and limited-time offer."
//       helperText="Describe your idea, product, service or campaign for AI."
//     />
//   );
// }
import FormTextArea from "../../../ui/form/FormTextArea";

export default function AIPromptField() {
  return (
    <FormTextArea
      name="ai_prompt"
      label="Describe your post"
      rows={3}
      placeholder="Describe your product, offer, campaign or idea..."
      helperText="Give AI enough context to create a relevant caption."
    />
  );
}