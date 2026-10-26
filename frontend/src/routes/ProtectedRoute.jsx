import { Navigate, Outlet } from "react-router-dom";
import { useAuthContext } from "../context/AuthContext";
import LoadingState from "../components/ui/LoadingState";

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuthContext();

  if (loading) {
    return <LoadingState label="LOADING DIGITALMARKETING CRM..." variant="viewport" />;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
