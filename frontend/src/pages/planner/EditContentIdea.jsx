// import { useEffect } from "react";
// import { useNavigate, useParams } from "react-router-dom";

// import { FormProvider, useForm } from "react-hook-form";
// import { zodResolver } from "@hookform/resolvers/zod";

// import { Paper, Divider } from "@mui/material";

// import EditContentIdeaHeader from "../../components/planner/edit/EditContentIdeaHeader";
// import IdeaDetailsForm from "../../components/planner/create/IdeaDetailsForm";
// import ContentDetailsForm from "../../components/planner/create/ContentDetailsForm";
// import EditContentIdeaFooter from "../../components/planner/edit/EditContentIdeaFooter";

// import { contentIdeaSchema } from "../../validation/contentIdea.schema";
// import { contentIdeaDefaultValues } from "../../constants/forms/contentIdeaDefaultValues";

// import contentPlannerService from "../../services/contentPlanner.service";

// export default function EditContentIdea() {
//   const navigate = useNavigate();

//   const { ideaId } = useParams();

//   const methods = useForm({
//     resolver: zodResolver(contentIdeaSchema),

//     defaultValues: contentIdeaDefaultValues,

//     mode: "onSubmit",
//   });

//   useEffect(() => {
//     loadIdea();
//   }, [ideaId]);

//   async function loadIdea() {
//     const idea = await contentPlannerService.getIdea(ideaId);

//     if (!idea) {
//       navigate("/planner");
//       return;
//     }

//     methods.reset({
//       organization: idea.organization_id,

//       title: idea.title,

//       platform: idea.platform,

//       target_publish_date: idea.target_publish_date,

//       content_type: idea.type,

//       campaign_goal: idea.goal,

//       description: idea.description,
//     });
//   }

//   async function onSubmit(data) {
//     console.log(data);

//     /*
//       Later

//       await contentPlannerService.updateIdea(
//         ideaId,
//         data
//       );

//       navigate("/planner");
//     */
//   }

//   return (
//     <FormProvider {...methods}>
//       <form onSubmit={methods.handleSubmit(onSubmit)}>
//         <EditContentIdeaHeader />

//         <Paper
//           elevation={0}
//           sx={{
//             maxWidth: "980px",
//             mx: "auto",
//             p: 4,
//             borderRadius: "24px",
//             border: "1px solid #E2E8F0",
//             bgcolor: "#FFFFFF",
//           }}
//         >
//           <IdeaDetailsForm />

//           <Divider sx={{ my: 5 }} />

//           <ContentDetailsForm />

//           <EditContentIdeaFooter onCancel={() => navigate("/planner")} />
//         </Paper>
//       </form>
//     </FormProvider>
//   );
// }

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { FormProvider, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Alert, Divider, Paper } from "@mui/material";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";

import EditContentIdeaHeader from "../../components/planner/edit/EditContentIdeaHeader";
import IdeaDetailsForm from "../../components/planner/create/IdeaDetailsForm";
import ContentDetailsForm from "../../components/planner/create/ContentDetailsForm";
import EditContentIdeaFooter from "../../components/planner/edit/EditContentIdeaFooter";
import PlannerLoadingState from "../../components/planner/PlannerLoadingState";
import PlannerErrorState from "../../components/planner/PlannerErrorState";
import PlannerEmptyState from "../../components/planner/PlannerEmptyState";
import { plannerFormDividerSx, plannerFormPaperSx } from "../../components/planner/plannerUiSx";

import { contentIdeaSchema } from "../../validation/contentIdea.schema";
import { contentIdeaDefaultValues } from "../../constants/forms/contentIdeaDefaultValues";

import contentPlannerService from "../../services/contentPlanner.service";
import { formatApiErrorMessage } from "../../utils/apiErrorMessage";

export default function EditContentIdea() {
  const navigate = useNavigate();
  const { ideaId } = useParams();

  const methods = useForm({
    resolver: zodResolver(contentIdeaSchema),
    defaultValues: contentIdeaDefaultValues,
    mode: "onSubmit",
  });

  const [organizations, setOrganizations] = useState([]);

  const [loading, setLoading] = useState(true);
  const [loadingOrganizations, setLoadingOrganizations] = useState(true);

  const [ideaLoadError, setIdeaLoadError] = useState(null);
  const [organizationsLoadError, setOrganizationsLoadError] = useState(null);
  const [ideaLoadedSuccessfully, setIdeaLoadedSuccessfully] = useState(false);
  const [organizationsLoadedSuccessfully, setOrganizationsLoadedSuccessfully] = useState(false);
  const [error, setError] = useState(null);

  const [submitting, setSubmitting] = useState(false);

  // ============================================================
  // LOAD ORGANIZATIONS
  // ============================================================

  const loadOrganizations = useCallback(async () => {
    try {
      setLoadingOrganizations(true);
      setOrganizationsLoadError(null);

      const response = await contentPlannerService.getContentPlanner();

      if (!response?.success) {
        throw new Error(response?.message || "Unable to load organizations.");
      }

      if (!Array.isArray(response?.data?.organizations)) {
        throw new Error("Organization data was not returned.");
      }

      const organizationList = response.data.organizations;

      setOrganizations(organizationList);
      setOrganizationsLoadedSuccessfully(true);
    } catch (error) {
      console.error("Failed to load Content Planner organizations:", error);

      setOrganizationsLoadError(formatApiErrorMessage(error, {
        fallback: "Unable to load organizations.",
      }));
    } finally {
      setLoadingOrganizations(false);
    }
  }, []);

  // ============================================================
  // LOAD IDEA
  // ============================================================

  const loadIdea = useCallback(async () => {
    if (!ideaId) {
      navigate("/planner", {
        replace: true,
      });

      return;
    }

    try {
      setLoading(true);
      setIdeaLoadError(null);

      const response = await contentPlannerService.getIdea(ideaId);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to load content idea.");
      }

      const idea = response?.data;

      if (!idea) {
        navigate("/planner", {
          replace: true,
        });

        return;
      }

      methods.reset({
        organization: idea.organization_id || "",
        social_account_ids: Array.isArray(idea.selected_social_accounts)
          ? idea.selected_social_accounts.map((account) => account.id)
          : [],
        caption: idea.caption || "",
        target_publish_date: idea.target_publish_date || "",
        target_publish_time: idea.target_publish_time || "",
        content_type: idea.content_type || idea.type || "",
        description: idea.description || "",
      });
      setIdeaLoadedSuccessfully(true);
    } catch (error) {
      console.error("Failed to load content idea:", error);

      if (error?.response?.status === 404) {
        navigate("/planner", {
          replace: true,
        });

        return;
      }

      setIdeaLoadError(formatApiErrorMessage(error, {
        fallback: "Unable to load content idea.",
      }));
    } finally {
      setLoading(false);
    }
  }, [ideaId, navigate, methods]);

  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (!active) return;
      loadIdea();
      loadOrganizations();
    });

    return () => {
      active = false;
    };
  }, [loadIdea, loadOrganizations]);

  // ============================================================
  // SUBMIT
  // ============================================================

  async function onSubmit(data) {
    if (!ideaId || submitting) {
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const response = await contentPlannerService.updateIdea(ideaId, data);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to update content idea.");
      }

      navigate("/planner");
    } catch (error) {
      console.error("Failed to update content idea:", error);

      setError(formatApiErrorMessage(error, {
        fallback: "Unable to update content idea.",
      }));
    } finally {
      setSubmitting(false);
    }
  }

  // ============================================================
  // LOADING
  // ============================================================

  if ((loading && !ideaLoadedSuccessfully) || (loadingOrganizations && !organizationsLoadedSuccessfully)) {
    return <PlannerLoadingState page="Edit Content Idea" />;
  }

  // ============================================================
  // ERROR
  // ============================================================

  if (ideaLoadError && !ideaLoadedSuccessfully) {
    return <PlannerErrorState message={ideaLoadError} onRetry={loadIdea} variant="page" />;
  }

  if (organizationsLoadError && !ideaLoadedSuccessfully) {
    return <PlannerErrorState message={organizationsLoadError} onRetry={loadOrganizations} variant="page" />;
  }

  if (!loading && !loadingOrganizations && !ideaLoadError && !organizationsLoadError && organizationsLoadedSuccessfully && organizations.length === 0) {
    return (
      <PlannerEmptyState
        icon={<BusinessOutlinedIcon />}
        title="No organizations available"
        description="An organization is required to edit this content idea."
        actionLabel="Create organization"
        onAction={() => navigate("/organizations/new")}
        sx={{ minHeight: 320 }}
      />
    );
  }

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <EditContentIdeaHeader />

        {loading && <PlannerLoadingState label="UPDATING CONTENT IDEA..." variant="inline" />}
        {loadingOrganizations && <PlannerLoadingState label="UPDATING ORGANIZATIONS..." variant="inline" />}
        {ideaLoadError && (
          <PlannerErrorState message={ideaLoadError} onRetry={loadIdea} variant="inline" />
        )}
        {organizationsLoadError && (
          <PlannerErrorState message={organizationsLoadError} onRetry={loadOrganizations} variant="inline" />
        )}
        {error && <Alert severity="error" sx={{ mb: 3, borderRadius: "12px", border: "1px solid #FECACA" }}>{error}</Alert>}

        <Paper
          elevation={0}
          sx={{
            ...plannerFormPaperSx,
            maxWidth: "980px",
          }}
        >
          <IdeaDetailsForm organizations={organizations} />

          <Divider sx={plannerFormDividerSx} />

          <ContentDetailsForm />

          <EditContentIdeaFooter
            loading={submitting}
            onCancel={() => {
              if (!submitting) {
                navigate("/planner");
              }
            }}
          />
        </Paper>
      </form>
    </FormProvider>
  );
}
