import { Navigate, Outlet } from "react-router-dom";
import { useAuthContext } from "../context/AuthContext";
import LoadingState from "../components/ui/LoadingState";

export default function PublicRoute() {
  const { isAuthenticated, loading } = useAuthContext();

  if (loading) {
    return <LoadingState label="LOADING DIGITALMARKETING CRM..." variant="viewport" />;
  }

  return isAuthenticated ? <Navigate to="/" replace /> : <Outlet />;
}
