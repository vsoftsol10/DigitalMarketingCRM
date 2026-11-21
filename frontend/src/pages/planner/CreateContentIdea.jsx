// import { FormProvider, useForm } from "react-hook-form";
// import { zodResolver } from "@hookform/resolvers/zod";

// import { Paper, Divider } from "@mui/material";

// import CreateContentIdeaHeader from "../../components/planner/create/CreateContentIdeaHeader";
// import IdeaDetailsForm from "../../components/planner/create/IdeaDetailsForm";
// import ContentDetailsForm from "../../components/planner/create/ContentDetailsForm";
// import CreateContentIdeaFooter from "../../components/planner/create/CreateContentIdeaFooter";
// import { contentIdeaSchema } from "../../validation/contentIdea.schema";
// import { contentIdeaDefaultValues } from "../../constants/forms/contentIdeaDefaultValues";

// import contentPlannerService from "../../services/contentPlanner.service";
// import { useNavigate } from "react-router-dom";

// export default function CreateContentIdea() {
//   const methods = useForm({
//     resolver: zodResolver(contentIdeaSchema),

//     defaultValues: contentIdeaDefaultValues,

//     mode: "onSubmit",
//   });

//   async function onSubmit(data) {
//     console.log(data);

//     /*
//       Later

//       await contentPlannerService.createIdea(data)

//     */
//   }
//   const navigate = useNavigate();

//   return (
//     <FormProvider {...methods}>
//       <form onSubmit={methods.handleSubmit(onSubmit)}>
//         <CreateContentIdeaHeader />

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

//           <CreateContentIdeaFooter onCancel={() => navigate("/planner")} />
//         </Paper>
//       </form>
//     </FormProvider>
//   );
// }

import { FormProvider, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Paper, Divider } from "@mui/material";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import CreateContentIdeaHeader from "../../components/planner/create/CreateContentIdeaHeader";
import IdeaDetailsForm from "../../components/planner/create/IdeaDetailsForm";
import ContentDetailsForm from "../../components/planner/create/ContentDetailsForm";
import CreateContentIdeaFooter from "../../components/planner/create/CreateContentIdeaFooter";
import PlannerLoadingState from "../../components/planner/PlannerLoadingState";
import PlannerErrorState from "../../components/planner/PlannerErrorState";
import PlannerEmptyState from "../../components/planner/PlannerEmptyState";
import { plannerFormDividerSx, plannerFormPaperSx } from "../../components/planner/plannerUiSx";

import { contentIdeaSchema } from "../../validation/contentIdea.schema";
import { contentIdeaDefaultValues } from "../../constants/forms/contentIdeaDefaultValues";

import contentPlannerService from "../../services/contentPlanner.service";
import { formatApiErrorMessage } from "../../utils/apiErrorMessage";

export default function CreateContentIdea() {
  const navigate = useNavigate();

  const [organizations, setOrganizations] = useState([]);
  const [loadingOrganizations, setLoadingOrganizations] = useState(true);
  const [organizationError, setOrganizationError] = useState(null);
  const [organizationsLoadedSuccessfully, setOrganizationsLoadedSuccessfully] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const methods = useForm({
    resolver: zodResolver(contentIdeaSchema),
    defaultValues: contentIdeaDefaultValues,
    mode: "onSubmit",
  });

  // ============================================================
  // LOAD ORGANIZATIONS
  // ============================================================

  const loadOrganizations = useCallback(async () => {
    try {
      setLoadingOrganizations(true);
      setOrganizationError(null);

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

      setOrganizationError(formatApiErrorMessage(error, {
        fallback: "Unable to load organizations.",
      }));
    } finally {
      setLoadingOrganizations(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) loadOrganizations();
    });

    return () => {
      active = false;
    };
  }, [loadOrganizations]);

  // ============================================================
  // SUBMIT
  // ============================================================

  async function onSubmit(data) {
    if (submitting) {
      return;
    }

    try {
      setSubmitting(true);
      setSubmitError(null);

      const response = await contentPlannerService.createIdea(data);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to create content idea.");
      }

      navigate("/planner");
    } catch (error) {
      console.error("Failed to create content idea:", error);

      setSubmitError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to create content idea.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  // ============================================================
  // LOADING
  // ============================================================

  if (loadingOrganizations && !organizationsLoadedSuccessfully) {
    return <PlannerLoadingState page="Create Content Idea" />;
  }

  if (organizationError && !organizationsLoadedSuccessfully) {
    return <PlannerErrorState message={organizationError} onRetry={loadOrganizations} variant="page" />;
  }

  if (!loadingOrganizations && !organizationError && organizationsLoadedSuccessfully && organizations.length === 0) {
    return (
      <PlannerEmptyState
        icon={<BusinessOutlinedIcon />}
        title="No organizations available"
        description="Create an organization before adding a content idea."
        actionLabel="Create organization"
        onAction={() => navigate("/organizations/new")}
        sx={{ minHeight: 320 }}
      />
    );
  }

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <CreateContentIdeaHeader />

        {loadingOrganizations && (
          <PlannerLoadingState label="UPDATING ORGANIZATIONS..." variant="inline" />
        )}
        {organizationError && (
          <PlannerErrorState
            message={organizationError}
            onRetry={loadOrganizations}
            variant="inline"
          />
        )}

        {submitError && (
          <Alert
            severity="error"
            sx={{
              mb: 3,
              borderRadius: "12px",
              border: "1px solid #FECACA",
            }}
          >
            {submitError}
          </Alert>
        )}

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

          <CreateContentIdeaFooter
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
