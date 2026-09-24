import { Alert, Box, CircularProgress, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useRef } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";

import SocialAccountCard from "../../post/create/SocialAccountCard";
import socialAccountService from "../../../services/social/socialAccount.service";
import { TYPOGRAPHY } from "../../../theme/typography";

export default function PublishAccountsField({ organizations = [] }) {
  const { control, setValue, formState: { errors } } = useFormContext();
  const organizationId = useWatch({ control, name: "organization" });
  const selectedAccountIds = useWatch({ control, name: "social_account_ids" }) || [];
  const previousOrganizationId = useRef();
  const organization = organizations.find((item) => item.id === organizationId);
  const organizationCode = organization?.organization_id;

  const { data, isLoading, error } = useQuery({
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

  const accounts = Array.isArray(data?.data)
    ? data.data.filter((account) => account.connected && account.valid)
    : [];

  function toggleAccount(accountId) {
    const next = selectedAccountIds.includes(accountId)
      ? selectedAccountIds.filter((id) => id !== accountId)
      : [...selectedAccountIds, accountId];
    setValue("social_account_ids", next, { shouldDirty: true, shouldValidate: true });
  }

  return (
    <Stack spacing={1}>
      <Typography sx={TYPOGRAPHY.inputLabel}>Publish Accounts<Typography component="span" sx={{ color: "#EF4444", ml: 0.5 }}>*</Typography></Typography>
      {!organizationId ? (
        <Alert severity="info" sx={{ borderRadius: "12px" }}>Select an organization to load its connected publish accounts.</Alert>
      ) : isLoading ? (
        <Box sx={{ py: 3, display: "flex", justifyContent: "center" }}><CircularProgress size={24} /></Box>
      ) : error ? (
        <Alert severity="error" sx={{ borderRadius: "12px" }}>Unable to load publish accounts.</Alert>
      ) : accounts.length === 0 ? (
        <Alert severity="warning" sx={{ borderRadius: "12px" }}>This organization has no connected, valid publish accounts.</Alert>
      ) : (
        <Grid container spacing={1.5}>
          {accounts.map((account) => (
            <Grid key={account.id} size={{ xs: 12, sm: 6 }}>
              <SocialAccountCard account={{ ...account, platform: String(account.platform).toUpperCase(), accountName: account.pageName }} selected={selectedAccountIds.includes(account.id)} onChange={toggleAccount} />
            </Grid>
          ))}
        </Grid>
      )}
      {errors.social_account_ids?.message && <Typography sx={{ ...TYPOGRAPHY.helperText, color: "#D32F2F" }}>{errors.social_account_ids.message}</Typography>}
    </Stack>
  );
}
