import SectionCard from "./SectionCard";
import FormSelect from "../../ui/form/FormSelect";
import { postMenuPaperSx } from "./postUiSx";

export default function OrganizationSection({
  organizations = [],
}) {
  return (
    <SectionCard
      title="Organization"
      description="Choose which client this post belongs to."
    >
      <FormSelect
        name="organization"
        label="Organization"
        required
        placeholder="Select Organization"
        MenuProps={{
          PaperProps: {
            sx: postMenuPaperSx,
          },
        }}
        options={organizations.map((organization) => ({
          value: organization.id,
          label: organization.name,
        }))}
      />
    </SectionCard>
  );
}
