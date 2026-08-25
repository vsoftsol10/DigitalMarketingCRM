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

import { Alert, Box, CircularProgress, Divider, Paper } from "@mui/material";

import EditContentIdeaHeader from "../../components/planner/edit/EditContentIdeaHeader";
import IdeaDetailsForm from "../../components/planner/create/IdeaDetailsForm";
import ContentDetailsForm from "../../components/planner/create/ContentDetailsForm";
import EditContentIdeaFooter from "../../components/planner/edit/EditContentIdeaFooter";

import { contentIdeaSchema } from "../../validation/contentIdea.schema";
import { contentIdeaDefaultValues } from "../../constants/forms/contentIdeaDefaultValues";

import contentPlannerService from "../../services/contentPlanner.service";

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

  const [error, setError] = useState(null);

  const [submitting, setSubmitting] = useState(false);

  // ============================================================
  // LOAD ORGANIZATIONS
  // ============================================================

  const loadOrganizations = useCallback(async () => {
    try {
      setLoadingOrganizations(true);

      const response = await contentPlannerService.getContentPlanner();

      if (!response?.success) {
        throw new Error(response?.message || "Unable to load organizations.");
      }

      const organizationList = Array.isArray(response?.data?.organizations)
        ? response.data.organizations
        : [];

      setOrganizations(organizationList);
    } catch (error) {
      console.error("Failed to load Content Planner organizations:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load organizations.",
      );

      setOrganizations([]);
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
      setError(null);

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
        title: idea.title || "",
        platform: idea.platform || "",
        target_publish_date: idea.target_publish_date || "",
        content_type: idea.type || "",
        campaign_goal: idea.goal || "",
        description: idea.description || "",
      });
    } catch (error) {
      console.error("Failed to load content idea:", error);

      if (error?.response?.status === 404) {
        navigate("/planner", {
          replace: true,
        });

        return;
      }

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load content idea.",
      );
    } finally {
      setLoading(false);
    }
  }, [ideaId, navigate, methods]);

  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    loadIdea();
    loadOrganizations();
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

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to update content idea.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  // ============================================================
  // LOADING
  // ============================================================

  if (loading || loadingOrganizations) {
    return (
      <Box
        sx={{
          minHeight: 500,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress size={30} />
      </Box>
    );
  }

  // ============================================================
  // ERROR
  // ============================================================

  if (error) {
    return (
      <Box
        sx={{
          maxWidth: 980,
          mx: "auto",
          p: 3,
        }}
      >
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <EditContentIdeaHeader />

        <Paper
          elevation={0}
          sx={{
            maxWidth: "980px",
            mx: "auto",

            p: 4,

            borderRadius: "24px",

            border: "1px solid #E2E8F0",

            bgcolor: "#FFFFFF",
          }}
        >
          <IdeaDetailsForm organizations={organizations} />

          <Divider sx={{ my: 5 }} />

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
