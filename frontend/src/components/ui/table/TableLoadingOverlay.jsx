import LoadingState from "../LoadingState";

export default function TableLoadingOverlay({ label = "LOADING CONTENT..." }) {
  return (
    <LoadingState label={label} variant="overlay" />
  );
}
