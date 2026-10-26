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
        MenuProps={{
          PaperProps: {
            sx: {
              mt: 0.75,
              border: "1px solid rgba(255,255,255,.94)",
              borderRadius: "15px",
              background:
                "linear-gradient(145deg, rgba(250,252,255,.98), rgba(237,244,255,.96))",
              boxShadow:
                "0 12px 24px rgba(75,96,151,.16), inset 0 1px 0 rgba(255,255,255,.98)",
              "& .MuiMenuItem-root": {
                minHeight: 42,
                mx: 0.6,
                borderRadius: "9px",
                color: "#344767",
                "&:hover": { backgroundColor: "rgba(222,234,255,.72)" },
                "&.Mui-selected": { backgroundColor: "rgba(220,230,255,.82)" },
              },
            },
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
