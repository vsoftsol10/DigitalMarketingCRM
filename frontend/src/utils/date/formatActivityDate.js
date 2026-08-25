export default function formatActivityDate(dateString) {
  if (!dateString) return "";

  const date = new Date(dateString);

  const now = new Date();

  const diff =
    now.getTime() - date.getTime();

  const days = Math.floor(
    diff / (1000 * 60 * 60 * 24)
  );

  if (days <= 30) {
    return `${days}d ago`;
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}