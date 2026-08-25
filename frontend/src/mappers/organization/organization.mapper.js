export function mapOrganizationOverview(
  response,
) {
  if (!response) return null;

  return {
    id: response.id,
    name: response.name,
    description: response.description,
  };
}