import FormTextArea from "../../../ui/form/FormTextArea";

export default function CaptionEditor() {
  return (
    <FormTextArea
      name="caption"
      label="Caption"
      required
      rows={8}
      placeholder="Write an engaging caption for your audience..."
      helperText="This caption will be published to all selected social platforms."
    />
  );
}