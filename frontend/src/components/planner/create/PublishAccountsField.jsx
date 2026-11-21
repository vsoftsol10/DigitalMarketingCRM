import { Alert, Button, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useRef } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";

import SocialAccountCard from "../../post/create/SocialAccountCard";
import socialAccountService from "../../../services/social/socialAccount.service";
import { TYPOGRAPHY } from "../../../theme/typography";
import PlannerLoadingState from "../PlannerLoadingState";
import formatApiErrorMessage from "../../../utils/apiErrorMessage";
import { plannerAlertSx } from "../plannerUiSx";

export default function PublishAccountsField({ organizations = [] }) {
  const { control, setValue, formState: { errors } } = useFormContext();
  const organizationId = useWatch({ control, name: "organization" });
  const selectedAccountIds = useWatch({ control, name: "social_account_ids" }) || [];
  const previousOrganizationId = useRef();
  const organization = organizations.find((item) => item.id === organizationId);
  const organizationCode = organization?.organization_id;

  const {
    data,
    isLoading,
    isFetching,
    isSuccess,
    error,
    refetch,
  } = useQuery({
    queryKey: ["planner-social-accounts", organizationCode],
    queryFn: ({ signal }) => socialAccountService.getOrganizationSocialAccounts(organizationCode, { signal }),
    enabled: Boolean(organizationCode),
  });

  useEffect(() => {
    if (previousOrganizationId.current !== undefined && previousOrganizationId.current !== organizationId) {
      setValue("social_account_ids", [], { shouldDirty: true, shouldValidate: true });
    }
    previousOrganizationId.current = organizationId;
  }, [organizationId, setValue]);

  const hasValidAccountResponse = Boolean(
    organizationCode
    && data?.success === true
    && Array.isArray(data.data),
  );
  const hasLoadedAccounts = hasValidAccountResponse;
  const accounts = hasLoadedAccounts
    ? data.data.filter((account) => account.connected && account.valid)
    : [];

  const retryButton = (
    <Button
      color="inherit"
      size="small"
      disabled={isFetching}
      onClick={() => { void refetch(); }}
      sx={{
        color: "#6941D9",
        textTransform: "none",
        fontWeight: 600,
        "&:hover": { background: "#F5F2FF" },
      }}
    >
      Retry
    </Button>
  );

  function toggleAccount(accountId) {
    const next = selectedAccountIds.includes(accountId)
      ? selectedAccountIds.filter((id) => id !== accountId)
      : [...selectedAccountIds, accountId];
    setValue("social_account_ids", next, { shouldDirty: true, shouldValidate: true });
  }

  return (
    <Stack
      spacing={1}
      sx={{
        minWidth: 0,
        p: { xs: 1.5, sm: 2 },
        borderRadius: "16px",
        background: "#F8FAFC",
        border: "1px solid #E5E9F1",
        boxShadow: "none",
      }}
    >
      <Typography sx={TYPOGRAPHY.inputLabel}>Publish Accounts<Typography component="span" sx={{ color: "#EF4444", ml: 0.5 }}>*</Typography></Typography>
      {!organizationId ? (
        <Alert severity="info" sx={plannerAlertSx}>Select an organization to load its connected publish accounts.</Alert>
      ) : !organizationCode ? (
        <Alert severity="error" sx={plannerAlertSx}>
          The selected organization could not be matched to its publish accounts.
        </Alert>
      ) : isLoading && !hasLoadedAccounts ? (
        <PlannerLoadingState label="LOADING PUBLISH ACCOUNTS..." variant="container" minHeight={72} />
      ) : error && !hasLoadedAccounts ? (
        <Alert
          severity="error"
          sx={plannerAlertSx}
          action={retryButton}
        >
          {formatApiErrorMessage(error, { fallback: "Unable to load publish accounts." })}
        </Alert>
      ) : isSuccess && !hasLoadedAccounts ? (
        <Alert severity="error" sx={plannerAlertSx} action={retryButton}>
          Publish account data was not returned in the expected format.
        </Alert>
      ) : !hasLoadedAccounts ? (
        <Alert severity="error" sx={plannerAlertSx}>
          Publish account data is unavailable until the selected organization can be verified.
        </Alert>
      ) : (
        <>
          {error && (
            <Alert
              severity="error"
              sx={plannerAlertSx}
              action={retryButton}
            >
              Could not refresh publish accounts. Previously loaded accounts remain available. {formatApiErrorMessage(error, { fallback: "Please try again." })}
            </Alert>
          )}
          {accounts.length === 0 ? (
            <Alert severity="warning" sx={plannerAlertSx}>This organization has no connected, valid publish accounts.</Alert>
          ) : (
            <Grid container spacing={1.5}>
              {accounts.map((account) => (
                <Grid key={account.id} size={{ xs: 12, sm: 6 }}>
                  <SocialAccountCard account={{ ...account, platform: String(account.platform).toUpperCase(), accountName: account.pageName }} selected={selectedAccountIds.includes(account.id)} onChange={toggleAccount} plannerStyle />
                </Grid>
              ))}
            </Grid>
          )}
        </>
      )}
      {errors.social_account_ids?.message && (
        <Typography
          sx={{
            ...TYPOGRAPHY.helperText,
            mt: 0.75,
            color: "#DC2626",
            fontSize: "13px",
            fontWeight: 500,
            lineHeight: 1.45,
            whiteSpace: "normal",
            overflowWrap: "anywhere",
          }}
        >
          {errors.social_account_ids.message}
        </Typography>
      )}
    </Stack>
  );
}
