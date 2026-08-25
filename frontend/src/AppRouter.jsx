import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/auth/Login";
import Dashboard from "./pages/dashboard/Dashboard";

import OrganizationList from "./pages/organizations/OrganizationList";
import CreateOrganization from "./pages/organizations/CreateOrganization";
import OrganizationOverview from "./pages/organizations/OrganizationOverview";

import ContentPlanner from "./pages/planner/ContentPlanner";
import Calendar from "./pages/calendar/Calendar";

import DMAutomation from "./pages/dm-automation/DMAutomation";
import AIScripts from "./pages/ai-scripts/AIScripts";
import Ads from "./pages/ads/Ads";

import Insights from "./pages/insights/Insights";
import Settings from "./pages/settings/Settings";

import DashboardLayout from "./layouts/DashboardLayout";

import ProtectedRoute from "./routes/ProtectedRoute";
import PublicRoute from "./routes/PublicRoute";
import EditOrganization from "./pages/organizations/EditOrganization";
import Plans from "./pages/plans/Plans";
import CreatePost from "./pages/posts/CreatePost";
import CreateContentIdea from "./pages/planner/CreateContentIdea";
import EditContentIdea from "./pages/planner/EditContentIdea";

// import Plans from "./pages/plans/Plans";
import CreatePlan from "./pages/plans/CreatePlan";
import PlanDetails from "./pages/plans/PlanDetails";
import EditPlan from "./pages/plans/EditPlan";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route element={<PublicRoute />}>
          <Route path="/login" element={<Login />} />
        </Route>

        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            {/* Dashboard */}
            <Route index element={<Dashboard />} />

            {/* Organizations */}
            <Route path="organizations" element={<OrganizationList />} />

            <Route path="organizations/new" element={<CreateOrganization />} />

            <Route
              path="organizations/:organizationId/edit"
              element={<EditOrganization />}
            />

            <Route
              path="organizations/:organizationId/overview"
              element={<OrganizationOverview />}
            />

            {/* Content */}
            {/* Content Planner */}

            <Route path="planner" element={<ContentPlanner />} />

            <Route path="planner/new" element={<CreateContentIdea />} />

            <Route path="planner/:ideaId/edit" element={<EditContentIdea />} />

            <Route path="calendar" element={<Calendar />} />

            {/* Engage */}
            <Route path="dm-automation" element={<DMAutomation />} />

            <Route path="posts" element={<CreatePost />} />

            <Route path="ai-scripts" element={<AIScripts />} />

            <Route path="ads" element={<Ads />} />

            {/* Analyze */}
            <Route path="insights" element={<Insights />} />

            {/* System */}

            <Route path="plans" element={<Plans />} />

            <Route path="plans/new" element={<CreatePlan />} />

            <Route path="plans/:planId" element={<PlanDetails />} />

            <Route path="plans/:planId/edit" element={<EditPlan />} />

            <Route path="settings" element={<Settings />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
