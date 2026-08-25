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
import { Alert, Box, CircularProgress, Paper, Divider } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import CreateContentIdeaHeader from "../../components/planner/create/CreateContentIdeaHeader";
import IdeaDetailsForm from "../../components/planner/create/IdeaDetailsForm";
import ContentDetailsForm from "../../components/planner/create/ContentDetailsForm";
import CreateContentIdeaFooter from "../../components/planner/create/CreateContentIdeaFooter";

import { contentIdeaSchema } from "../../validation/contentIdea.schema";
import { contentIdeaDefaultValues } from "../../constants/forms/contentIdeaDefaultValues";

import contentPlannerService from "../../services/contentPlanner.service";

export default function CreateContentIdea() {
  const navigate = useNavigate();

  const [organizations, setOrganizations] = useState([]);
  const [loadingOrganizations, setLoadingOrganizations] = useState(true);
  const [organizationError, setOrganizationError] = useState(null);

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

      const organizationList = Array.isArray(response?.data?.organizations)
        ? response.data.organizations
        : [];

      setOrganizations(organizationList);
    } catch (error) {
      console.error("Failed to load Content Planner organizations:", error);

      setOrganizationError(
        error?.response?.data?.message ||
          error?.message ||
          "Unable to load organizations.",
      );

      setOrganizations([]);
    } finally {
      setLoadingOrganizations(false);
    }
  }, []);

  useEffect(() => {
    loadOrganizations();
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

  if (loadingOrganizations) {
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

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <CreateContentIdeaHeader />

        {organizationError && (
          <Alert
            severity="error"
            sx={{
              mb: 3,
              borderRadius: "12px",
            }}
          >
            {organizationError}
          </Alert>
        )}

        {submitError && (
          <Alert
            severity="error"
            sx={{
              mb: 3,
              borderRadius: "12px",
            }}
          >
            {submitError}
          </Alert>
        )}

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
