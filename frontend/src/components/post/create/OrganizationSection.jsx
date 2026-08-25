import SectionCard from "./SectionCard";
import FormSelect from "../../ui/form/FormSelect";

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
        options={organizations.map((organization) => ({
          value: organization.id,
          label: organization.name,
        }))}
      />
    </SectionCard>
  );
}