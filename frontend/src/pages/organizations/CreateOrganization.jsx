import { Alert, Box, Divider, Paper } from "@mui/material";

import { FormProvider, useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";

import CreateHeader from "../../components/organization/create/CreateHeader";
import OrganizationDetailsForm from "../../components/organization/create/OrganizationDetailsForm";
import PrimaryContactForm from "../../components/organization/create/PrimaryContactForm";
import SubscriptionForm from "../../components/organization/create/SubscriptionForm";
import CreateOrganizationFooter from "../../components/organization/create/CreateOrganizationFooter";
import LoadingState from "../../components/ui/LoadingState";
import FormSection from "../../components/ui/form/FormSection";
import {
  glassFormDividerSx,
  glassFormPaperSx,
  glassFormSectionSx,
} from "../../components/ui/form/glassFormSx";

import { organizationSchema } from "../../validation/organization.schema";
import { organizationDefaultValues } from "../../constants/forms/organizationDefaultValues";

import organizationService from "../../services/organization/organization.service";
import plansService from "../../services/plans.service";

export default function CreateOrganization() {
  const navigate = useNavigate();

  // ============================================================
  // FORM
  // ============================================================

  const methods = useForm({
    resolver: zodResolver(organizationSchema),

    defaultValues: organizationDefaultValues,

    mode: "onSubmit",
  });

  const {
    handleSubmit,
    setError,
    clearErrors,
    formState: { isSubmitting, errors },
  } = methods;

  // ============================================================
  // PLANS
  // ============================================================

  const [activePlans, setActivePlans] = useState([]);

  const [plansLoading, setPlansLoading] = useState(true);

  const [plansError, setPlansError] = useState(null);

  // ============================================================
  // LOAD ACTIVE PLANS
  // ============================================================

  useEffect(() => {
    let mounted = true;

    async function loadActivePlans() {
      try {
        setPlansLoading(true);

        setPlansError(null);

        const plans = await plansService.getPlans({
          status: "active",
        });

        if (!mounted) {
          return;
        }

        if (!Array.isArray(plans)) {
          throw new Error("Invalid plans response.");
        }

        setActivePlans(plans);
      } catch (error) {
        console.error("Failed to load active plans:", error);

        if (mounted) {
          setPlansError(
            error?.response?.data?.message ||
              error?.message ||
              "Unable to load subscription plans.",
          );

          setActivePlans([]);
        }
      } finally {
        if (mounted) {
          setPlansLoading(false);
        }
      }
    }

    loadActivePlans();

    return () => {
      mounted = false;
    };
  }, []);

  // ============================================================
  // SUBMIT
  // ============================================================

  const onSubmit = async (data) => {
    clearErrors("root.server");

    try {
      const response = await organizationService.createOrganization(data);

      if (!response?.success) {
        throw new Error(response?.message || "Unable to create organization.");
      }

      const organization = response?.data;

      const organizationId = organization?.organization_id;

      if (!organizationId) {
        throw new Error(
          "Organization was created, but the organization ID was not returned.",
        );
      }

      // --------------------------------------------------------
      // IMPORTANT
      // --------------------------------------------------------
      // Social accounts are NOT connected during organization
      // creation.
      //
      // Organization must exist first because the backend
      // SocialAccount belongs to an Organization.
      //
      // After creation we navigate to the overview page where
      // social account OAuth connection can be started.
      // --------------------------------------------------------

      navigate(`/organizations/${organizationId}/overview`);
    } catch (error) {
      console.error("Failed to create organization:", error);

      const responseData = error?.response?.data;

      const backendErrors = responseData?.errors;

      // ========================================================
      // BACKEND FIELD VALIDATION ERRORS
      // ========================================================

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

      // ========================================================
      // GENERAL SERVER ERROR
      // ========================================================

      const serverMessage =
        responseData?.message ||
        error?.message ||
        "Unable to create organization. Please try again.";

      setError("root.server", {
        type: "server",
        message: serverMessage,
      });
    }
  };

  // ============================================================
  // SERVER ERROR
  // ============================================================

  const serverError = errors?.root?.server?.message;

  // ============================================================
  // CREATE BUTTON LOADING STATE
  // ============================================================

  const formLoading = isSubmitting || plansLoading || activePlans.length === 0;

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        {/* ====================================================
            HEADER
        ==================================================== */}

        <CreateHeader />

        {/* ====================================================
            SERVER ERROR
        ==================================================== */}

        {serverError && (
          <Alert
            severity="error"
            sx={{
              maxWidth: "980px",

              mx: "auto",

              mb: 3,

              borderRadius: "16px",
              border: "1px solid rgba(255,255,255,.85)",
              boxShadow: "0 6px 16px rgba(77, 59, 75, .08)",
            }}
          >
            {serverError}
          </Alert>
        )}

        {/* ====================================================
            PLANS ERROR
        ==================================================== */}

        {plansError && (
          <Alert
            severity="error"
            sx={{
              maxWidth: "980px",

              mx: "auto",

              mb: 3,

              borderRadius: "16px",
              border: "1px solid rgba(255,255,255,.85)",
              boxShadow: "0 6px 16px rgba(77, 59, 75, .08)",
            }}
          >
            {plansError}
          </Alert>
        )}

        {/* ====================================================
            FORM CONTAINER
        ==================================================== */}

        <Paper
          elevation={0}
          sx={{
            ...glassFormPaperSx,
            maxWidth: "980px",
          }}
        >
          {/* ==================================================
              ORGANIZATION DETAILS
          ================================================== */}

          <OrganizationDetailsForm />

          <Divider sx={glassFormDividerSx} />

          {/* ==================================================
              PRIMARY CONTACT
          ================================================== */}

          <PrimaryContactForm />

          <Divider sx={glassFormDividerSx} />

          {/* ==================================================
              SUBSCRIPTION
          ================================================== */}

          <Box sx={glassFormSectionSx}>
            <FormSection
              title="Subscription"
              description="Configure the organization's subscription plan and billing."
              spacing={2.5}
            >
              {plansLoading ? (
                <LoadingState
                  label="LOADING SUBSCRIPTION PLANS..."
                  variant="container"
                  minHeight={56}
                />
              ) : (
                <SubscriptionForm plans={activePlans} />
              )}
            </FormSection>
          </Box>

          {/* ==================================================
              SOCIAL ACCOUNTS
              
              DO NOT RENDER HERE.
              
              Organization doesn't have an ID until the create
              request succeeds.
              
              Social accounts will be connected from:
              
              /organizations/:organizationId/overview
              
              using:
              
              components/organization/social/
          ================================================== */}

          {/* ==================================================
              FOOTER
          ================================================== */}

          <CreateOrganizationFooter loading={formLoading} />
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

    billing_cycle: "billing_cycle",
  };

  return fieldMap[field] || field;
}
