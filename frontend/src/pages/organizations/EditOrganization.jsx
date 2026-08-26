import { Alert, Box, CircularProgress, Divider, Paper } from "@mui/material";

import { FormProvider, useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import { useEffect, useState } from "react";

import { useNavigate, useParams } from "react-router-dom";

// ============================================================
// ORGANIZATION COMPONENTS
// ============================================================

import EditHeader from "../../components/organization/edit/EditHeader";

import UpdateOrganizationFooter from "../../components/organization/edit/UpdateOrganizationFooter";

import OrganizationDetailsForm from "../../components/organization/create/OrganizationDetailsForm";

import PrimaryContactForm from "../../components/organization/create/PrimaryContactForm";

// ============================================================
// VALIDATION / CONSTANTS
// ============================================================

import { organizationSchema } from "../../validation/organization.schema";

import { organizationDefaultValues } from "../../constants/forms/organizationDefaultValues";

// ============================================================
// SERVICES
// ============================================================

import organizationService from "../../services/organization/organization.service";

// ============================================================
// COMPONENT
// ============================================================

export default function EditOrganization() {
  const navigate = useNavigate();

  const { organizationId } = useParams();

  // ==========================================================
  // ORGANIZATION STATE
  // ==========================================================

  const [loadingOrganization, setLoadingOrganization] = useState(true);

  const [loadError, setLoadError] = useState(null);

  // ==========================================================
  // FORM
  // ==========================================================

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

    formState: { isSubmitting, errors },
  } = methods;

  // ==========================================================
  // LOAD ORGANIZATION
  // ==========================================================

  useEffect(() => {
    let isMounted = true;

    const loadOrganization = async () => {
      // --------------------------------------------------------
      // ORGANIZATION ID VALIDATION
      // --------------------------------------------------------

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

        // ------------------------------------------------------
        // GET ORGANIZATION
        // ------------------------------------------------------

        const response =
          await organizationService.getOrganization(organizationId);

        if (!response?.success) {
          throw new Error(response?.message || "Unable to load organization.");
        }

        const organization = response?.data;

        if (!organization) {
          throw new Error("Organization data was not returned.");
        }

        // ------------------------------------------------------
        // RESET FORM
        // ------------------------------------------------------

        if (isMounted) {
          reset({
            ...organizationDefaultValues,

            ...organization,

            // ==================================================
            // ORGANIZATION
            // ==================================================

            name: organization.name ?? "",

            description: organization.description ?? "",

            industry: organization.industry ?? "",

            website: organization.website ?? "",

            location: organization.location ?? "",

            logo_color:
              organization.logo_color ?? organizationDefaultValues.logo_color,

            organization_status: organization.organization_status ?? "ACTIVE",

            // ==================================================
            // PRIMARY CONTACT
            // ==================================================

            contact_name: organization.contact_name ?? "",

            contact_email: organization.contact_email ?? "",

            contact_phone: organization.contact_phone ?? "",

            // ==================================================
            // SOCIAL ACCOUNTS
            // ==================================================

            /*
             * Social accounts are NOT edited from this form.
             *
             * They are managed separately from the
             * Organization Overview / Social Accounts UI.
             *
             * We keep them in form state only if the
             * organization API returns them.
             */

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

  // ==========================================================
  // INVALID SUBMIT
  // ==========================================================

  const onInvalidSubmit = (formErrors) => {
    console.log("Edit organization validation errors:", formErrors);
  };

  // ==========================================================
  // SUBMIT
  // ==========================================================

  const onSubmit = async (data) => {
    clearErrors("root.server");

    // --------------------------------------------------------
    // ORGANIZATION ID VALIDATION
    // --------------------------------------------------------

    if (!organizationId) {
      setError("root.server", {
        type: "server",

        message: "Organization ID is missing.",
      });

      return;
    }

    // --------------------------------------------------------
    // REMOVE NON-EDITABLE / SEPARATE DATA
    // --------------------------------------------------------
    //
    // Subscription is intentionally NOT editable here.
    //
    // Social accounts are also managed separately.
    //
    // Therefore they should not be sent through the
    // organization update endpoint.
    // --------------------------------------------------------

    const {
      subscription_plan,
      billing_cycle,
      subscription_status,
      subscription_start,
      subscription_expiry,
      social_accounts,

      ...organizationPayload
    } = data;

    try {
      // ------------------------------------------------------
      // UPDATE ORGANIZATION
      // ------------------------------------------------------

      const response = await organizationService.updateOrganization(
        organizationId,
        organizationPayload,
      );

      if (!response?.success) {
        throw new Error(response?.message || "Unable to update organization.");
      }

      // ------------------------------------------------------
      // GET UPDATED ORGANIZATION ID
      // ------------------------------------------------------

      const updatedOrganization = response?.data;

      const updatedOrganizationId =
        updatedOrganization?.organization_id || organizationId;

      // ------------------------------------------------------
      // GO TO OVERVIEW
      // ------------------------------------------------------

      navigate(`/organizations/${updatedOrganizationId}/overview`);
    } catch (error) {
      console.error("Failed to update organization:", error);

      const responseData = error?.response?.data;

      const backendErrors = responseData?.errors;

      // ======================================================
      // BACKEND FIELD ERRORS
      // ======================================================

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

      // ======================================================
      // GENERAL SERVER ERROR
      // ======================================================

      setError("root.server", {
        type: "server",

        message:
          responseData?.message ||
          error?.message ||
          "Unable to update organization. Please try again.",
      });
    }
  };

  // ==========================================================
  // LOADING STATE
  // ==========================================================

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

  // ==========================================================
  // ORGANIZATION LOAD ERROR
  // ==========================================================

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

  // ==========================================================
  // SERVER ERROR
  // ==========================================================

  const serverError = errors?.root?.server?.message;

  // ==========================================================
  // FORM ERROR COUNT
  // ==========================================================

  const hasFormErrors = Object.keys(errors).length > 0;

  // ==========================================================
  // FORM LOADING
  // ==========================================================

  const formLoading = isSubmitting;

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onSubmit, onInvalidSubmit)} noValidate>
        {/* ==================================================
            HEADER
        ================================================== */}

        <EditHeader loading={formLoading} />

        {/* ==================================================
            SERVER ERROR
        ================================================== */}

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

        {/* ==================================================
            VALIDATION ERROR
        ================================================== */}

        {hasFormErrors && !serverError && (
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

        {/* ==================================================
            FORM CONTAINER
        ================================================== */}

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
          {/* ==================================================
              ORGANIZATION DETAILS
          ================================================== */}

          <OrganizationDetailsForm />

          <Divider sx={{ my: 5 }} />

          {/* ==================================================
              PRIMARY CONTACT
          ================================================== */}

          <PrimaryContactForm />

          {/* ==================================================
              SUBSCRIPTION
          ================================================== */}

          {/*
            Subscription editing is intentionally removed
            from Organization Edit.

            Subscription changes should be handled through
            the dedicated Subscription Management flow.
          */}

          <Divider sx={{ my: 5 }} />

          {/* ==================================================
              FOOTER
          ================================================== */}

          <UpdateOrganizationFooter loading={formLoading} />
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
  };

  return fieldMap[field] || field;
}
