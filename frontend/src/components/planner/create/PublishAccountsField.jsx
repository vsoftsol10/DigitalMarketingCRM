import { Alert, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useRef } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";

import SocialAccountCard from "../../post/create/SocialAccountCard";
import socialAccountService from "../../../services/social/socialAccount.service";
import { TYPOGRAPHY } from "../../../theme/typography";
import LoadingState from "../../ui/LoadingState";

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
    <Stack
      spacing={1}
      sx={{
        minWidth: 0,
        p: { xs: 1.5, sm: 2 },
        borderRadius: "16px",
        background: "linear-gradient(145deg, rgba(235,243,255,.7), rgba(255,255,255,.7))",
        border: "1px solid rgba(255,255,255,.94)",
        boxShadow: "0 5px 14px rgba(73,99,153,.08), inset 0 1px 0 rgba(255,255,255,.98)",
      }}
    >
      <Typography sx={TYPOGRAPHY.inputLabel}>Publish Accounts<Typography component="span" sx={{ color: "#EF4444", ml: 0.5 }}>*</Typography></Typography>
      {!organizationId ? (
        <Alert severity="info" sx={{ borderRadius: "12px" }}>Select an organization to load its connected publish accounts.</Alert>
      ) : isLoading ? (
        <LoadingState label="LOADING PUBLISH ACCOUNTS..." variant="container" minHeight={72} />
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
