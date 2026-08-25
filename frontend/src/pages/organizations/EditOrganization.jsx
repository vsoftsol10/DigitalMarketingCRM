// import { FormProvider, useForm } from "react-hook-form";
// import { zodResolver } from "@hookform/resolvers/zod";
// import { Paper, Divider } from "@mui/material";
// import EditHeader from "../../components/organization/edit/EditHeader";
// import UpdateOrganizationFooter from "../../components/organization/edit/UpdateOrganizationFooter";
// import OrganizationDetailsForm from "../../components/organization/create/OrganizationDetailsForm";
// import PrimaryContactForm from "../../components/organization/create/PrimaryContactForm";
// import SubscriptionForm from "../../components/organization/create/SubscriptionForm";
// import SocialAccountsForm from "../../components/organization/create/SocialAccountsForm";
// import { organizationSchema } from "../../validation/organization.schema";
// import { organizationDefaultValues } from "../../constants/forms/organizationDefaultValues";
// import { useParams } from "react-router-dom";
// import { useEffect } from "react";
// import { ORGANIZATIONS } from "../../data/organizations";
// export default function EditOrganization() {
//   /**
//    * Later
//    *
//    * const { organizationId } = useParams()
//    * const { data } = useGetOrganization(organizationId)
//    *
//    * reset(data)
//    */

//   const methods = useForm({
//     resolver: zodResolver(organizationSchema),

//     defaultValues: organizationDefaultValues,

//     mode: "onSubmit",
//   });
//   const { organizationId } = useParams();

//   const organization = ORGANIZATIONS.find((item) => item.id === organizationId);

//   useEffect(() => {
//     if (organization) {
//       methods.reset(organization);
//     }
//   }, [organization, methods]);

//   const onSubmit = async (data) => {
//     console.log("Update Organization");

//     console.log(data);

//     /**
//      *
//      * await organizationService.update(
//      *      organizationId,
//      *      data
//      * )
//      *
//      */
//   };

//   return (
//     <FormProvider {...methods}>
//       <form onSubmit={methods.handleSubmit(onSubmit)}>
//         <EditHeader />

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
//           <OrganizationDetailsForm />

//           <Divider sx={{ my: 5 }} />

//           <PrimaryContactForm />

//           <Divider sx={{ my: 5 }} />

//           <SubscriptionForm />

//           <Divider sx={{ my: 5 }} />

//           <SocialAccountsForm />

//           <UpdateOrganizationFooter />
//         </Paper>
//       </form>
//     </FormProvider>
//   );
// }

import { Alert, Box, CircularProgress, Divider, Paper } from "@mui/material";

import { FormProvider, useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import { useNavigate, useParams } from "react-router-dom";

import { useEffect, useState } from "react";

import EditHeader from "../../components/organization/edit/EditHeader";
import UpdateOrganizationFooter from "../../components/organization/edit/UpdateOrganizationFooter";

import OrganizationDetailsForm from "../../components/organization/create/OrganizationDetailsForm";
import PrimaryContactForm from "../../components/organization/create/PrimaryContactForm";
import SubscriptionForm from "../../components/organization/create/SubscriptionForm";
import SocialAccountsForm from "../../components/organization/create/SocialAccountsForm";

import { organizationSchema } from "../../validation/organization.schema";
import { organizationDefaultValues } from "../../constants/forms/organizationDefaultValues";

import organizationService from "../../services/organization/organization.service";

export default function EditOrganization() {
  const navigate = useNavigate();

  const { organizationId } = useParams();

  const [loadingOrganization, setLoadingOrganization] = useState(true);

  const [loadError, setLoadError] = useState(null);

  const methods = useForm({
    resolver: zodResolver(organizationSchema),

    defaultValues: organizationDefaultValues,

    mode: "onSubmit",
  });

  const {
    reset,
    setError,
    clearErrors,
    handleSubmit,
    formState: { isSubmitting },
  } = methods;

  // ============================================================
  // LOAD ORGANIZATION
  // ============================================================

  useEffect(() => {
    let isMounted = true;

    const loadOrganization = async () => {
      if (!organizationId) {
        if (isMounted) {
          setLoadError("Organization ID is missing.");
          setLoadingOrganization(false);
        }

        return;
      }

      try {
        setLoadingOrganization(true);
        setLoadError(null);

        const response =
          await organizationService.getOrganization(organizationId);

        if (!response?.success) {
          throw new Error(response?.message || "Unable to load organization.");
        }

        const organization = response?.data;

        if (!organization) {
          throw new Error("Organization data was not returned.");
        }

        if (isMounted) {
          reset({
            ...organizationDefaultValues,
            ...organization,

            name: organization.name ?? "",
            description: organization.description ?? "",
            industry: organization.industry ?? "",
            website: organization.website ?? "",
            location: organization.location ?? "",
            logo_color:
              organization.logo_color ?? organizationDefaultValues.logo_color,
            organization_status: organization.organization_status ?? "ACTIVE",

            contact_name: organization.contact_name ?? "",
            contact_email: organization.contact_email ?? "",
            contact_phone: organization.contact_phone ?? "",

            subscription_plan: organization.subscription_plan ?? "BASIC",
            billing_cycle: organization.billing_cycle ?? "monthly",
            subscription_status: organization.subscription_status ?? "trial",

            subscription_start: organization.subscription_start ?? "",

            subscription_expiry: organization.subscription_expiry ?? "",

            social_accounts: Array.isArray(organization.social_accounts)
              ? organization.social_accounts
              : [],
          });
        }
      } catch (error) {
        console.error("Failed to load organization:", error);

        if (isMounted) {
          setLoadError(
            error?.response?.data?.message ||
              error?.message ||
              "Unable to load organization.",
          );
        }
      } finally {
        if (isMounted) {
          setLoadingOrganization(false);
        }
      }
    };

    loadOrganization();

    return () => {
      isMounted = false;
    };
  }, [organizationId, reset]);

  // ============================================================
  // UPDATE
  // ============================================================
  const onInvalidSubmit = (formErrors) => {
    console.log("Edit organization validation errors:", formErrors);
  };

  const onSubmit = async (data) => {
    console.log("Edit organization submit payload:", data);

    clearErrors("root.server");

    if (!organizationId) {
      setError("root.server", {
        type: "server",
        message: "Organization ID is missing.",
      });

      return;
    }

    try {
      const response = await organizationService.updateOrganization(
        organizationId,
        data,
      );

      if (!response?.success) {
        throw new Error(response?.message || "Unable to update organization.");
      }

      const updatedOrganization = response?.data;

      const updatedOrganizationId =
        updatedOrganization?.organization_id || organizationId;

      navigate(`/organizations/${updatedOrganizationId}/overview`);
    } catch (error) {
      console.error("Failed to update organization:", error);

      const responseData = error?.response?.data;

      const backendErrors = responseData?.errors;

      if (backendErrors && typeof backendErrors === "object") {
        Object.entries(backendErrors).forEach(([field, messages]) => {
          const message = Array.isArray(messages)
            ? messages[0]
            : String(messages);

          const frontendField = mapBackendFieldToFrontend(field);

          if (frontendField && frontendField !== "root.server") {
            setError(frontendField, {
              type: "server",
              message,
            });
          }
        });
      }

      setError("root.server", {
        type: "server",
        message:
          responseData?.message ||
          error?.message ||
          "Unable to update organization. Please try again.",
      });
    }
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (loadingOrganization) {
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
  // LOAD ERROR
  // ============================================================

  if (loadError) {
    return (
      <Box
        sx={{
          maxWidth: "980px",
          mx: "auto",
          p: 3,
        }}
      >
        <Alert severity="error">{loadError}</Alert>
      </Box>
    );
  }

  // ============================================================
  // SERVER ERROR
  // ============================================================

  const serverError = methods.formState.errors?.root?.server?.message;

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onSubmit, onInvalidSubmit)} noValidate>
        <EditHeader loading={isSubmitting} />

        {serverError && (
          <Alert
            severity="error"
            sx={{
              maxWidth: "980px",
              mx: "auto",
              mb: 3,
              borderRadius: "12px",
            }}
          >
            {serverError}
          </Alert>
        )}
        {Object.keys(methods.formState.errors).length > 0 && (
          <Alert
            severity="warning"
            sx={{
              maxWidth: "980px",
              mx: "auto",
              mb: 3,
              borderRadius: "12px",
            }}
          >
            Please fix the highlighted fields before saving.
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
          <OrganizationDetailsForm />

          <Divider sx={{ my: 5 }} />

          <PrimaryContactForm />

          <Divider sx={{ my: 5 }} />

          <SubscriptionForm />

          <Divider sx={{ my: 5 }} />

          <SocialAccountsForm />

          <UpdateOrganizationFooter loading={isSubmitting} />
        </Paper>
      </form>
    </FormProvider>
  );
}

// ============================================================
// BACKEND → FRONTEND FIELD MAPPING
// ============================================================

function mapBackendFieldToFrontend(field) {
  const fieldMap = {
    status: "organization_status",

    contact_person: "contact_name",
    email: "contact_email",
    phone: "contact_phone",

    plan: "subscription_plan",

    start_date: "subscription_start",

    expiry_date: "subscription_expiry",
  };

  return fieldMap[field] || field;
}
