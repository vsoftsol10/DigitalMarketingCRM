import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import { Alert, Box, Button, CircularProgress, LinearProgress, Stack, Typography } from "@mui/material";

import insightsService from "../../services/insights.service";
import InsightsHeader from "../../components/insights/InsightsHeader";
import InsightsStats from "../../components/insights/InsightsStats";
import PostPerformanceCard from "../../components/insights/PostPerformanceCard";
import ContentPerformanceCard from "../../components/insights/ContentPerformanceCard";
import InsightsExportDialog from "../../components/reports/InsightsExportDialog";

const PERIOD_DAYS = { "7D": 7, "30D": 30, "28D": 28 };
const ACTIVE_SYNC_STATUSES = ["queued", "syncing"];
const TERMINAL_SYNC_STATUSES = ["complete", "partial", "failed"];

function isActiveSyncRunning(activeSync) {
  if (!activeSync) return false;
  const stageStatuses = [activeSync.account_status, activeSync.content_status];
  if (stageStatuses.every((status) => TERMINAL_SYNC_STATUSES.includes(status))) return false;
  return ACTIVE_SYNC_STATUSES.includes(activeSync.status)
    || stageStatuses.some((status) => ACTIVE_SYNC_STATUSES.includes(status));
}

const accountSnapshotKey = (scope) => [
  "insights-account-snapshot",
  scope.organizationId,
  scope.socialAccountId,
  scope.duration,
  scope.platform,
];
const contentSnapshotKey = (scope) => [
  "insights-content-snapshot",
  scope.organizationId,
  scope.socialAccountId,
  scope.duration,
  scope.platform,
];
const scopeKey = (scope) => JSON.stringify([
  scope.organizationId,
  scope.socialAccountId,
  scope.duration,
  scope.platform,
]);

function formatSnapshotRange(since, until) {
  if (!since || !until) return "";
  const start = dayjs(since);
  const end = dayjs(until);
  if (!start.isValid() || !end.isValid()) return "";
  const startLabel = start.format("MMM D, YYYY");
  const endLabel = end.format("MMM D, YYYY");
  return startLabel === endLabel ? startLabel : `${startLabel} – ${endLabel}`;
}

export default function Insights() {
  const queryClient = useQueryClient();
  const [organizationId, setOrganizationId] = useState("");
  const [duration, setDuration] = useState("30D");
  const [platform, setPlatform] = useState("");
  const [accountId, setAccountId] = useState("");
  const [exportMode, setExportMode] = useState("");
  const [contentPage, setContentPage] = useState(1);
  const [activeSyncScopeKeys, setActiveSyncScopeKeys] = useState(() => new Set());
  const [finalizingSyncScopes, setFinalizingSyncScopes] = useState(() => new Set());
  const activeSyncScopes = useRef(new Set());
  const finalizingSyncScopesRef = useRef(new Set());

  const dateRange = useMemo(() => {
    const until = dayjs().format("YYYY-MM-DD");
    const since = dayjs().subtract(PERIOD_DAYS[duration] - 1, "day").format("YYYY-MM-DD");
    return { since, until };
  }, [duration]);

  const organizationsQuery = useQuery({
    queryKey: ["insights-organizations"],
    queryFn: ({ signal }) => insightsService.getOrganizations({ signal }),
  });

  const accountsQuery = useQuery({
    queryKey: ["insights-accounts", organizationId],
    queryFn: ({ signal }) => insightsService.getAccounts(organizationId, { signal }),
    enabled: Boolean(organizationId),
  });

  const allAccounts = Array.isArray(accountsQuery.data) ? accountsQuery.data : [];
  const supportedAccounts = allAccounts.filter((account) =>
    ["instagram", "facebook"].includes(String(account.platform || "").toLowerCase()),
  );
  const selectedAccount = supportedAccounts.find((account) => String(account.id) === accountId);
  const selectedPlatform = String(selectedAccount?.platform || "").toLowerCase();
  const selected = Boolean(organizationId && accountId && selectedAccount);
  const currentScope = useMemo(() => selected ? ({
    organizationId,
    socialAccountId: accountId,
    duration,
    since: dateRange.since,
    until: dateRange.until,
    platform: selectedPlatform,
  }) : null, [accountId, dateRange.since, dateRange.until, duration, organizationId, selected, selectedPlatform]);
  const currentScopeKey = currentScope ? scopeKey(currentScope) : "";

  const accountSnapshotQuery = useQuery({
    queryKey: ["insights-account-snapshot", organizationId, accountId, duration, selectedPlatform],
    queryFn: ({ signal }) => insightsService.getAccountSnapshot(
      organizationId,
      accountId,
      { ...dateRange, platform: selectedPlatform, signal },
    ),
    enabled: selected,
    retry: false,
    placeholderData: undefined,
    refetchInterval: (query) => isActiveSyncRunning(query.state.data?.freshness?.active_sync) ? 5000 : false,
    refetchIntervalInBackground: false,
  });

  const activeSync = accountSnapshotQuery.data?.freshness?.active_sync;
  const activeSyncStatus = activeSync?.status;
  const accountSyncStatus = activeSyncStatus || accountSnapshotQuery.data?.freshness?.sync?.status;

  const contentSnapshotQuery = useQuery({
    queryKey: ["insights-content-snapshot", organizationId, accountId, duration, selectedPlatform, contentPage],
    queryFn: ({ signal }) => insightsService.getContentSnapshot(
      organizationId,
      accountId,
      { ...dateRange, platform: selectedPlatform, page: contentPage, signal },
    ),
    enabled: selected,
    retry: false,
    placeholderData: undefined,
  });

  const syncMutation = useMutation({
    mutationFn: (scope) => insightsService.requestSync(
      scope.organizationId,
      scope.socialAccountId,
      scope,
    ),
    retry: false,
    onSuccess: async (response, scope) => {
      const key = accountSnapshotKey(scope);
      if (response.status === 202) {
        await Promise.all([
          queryClient.fetchQuery({
            queryKey: key,
            queryFn: ({ signal }) => insightsService.getAccountSnapshot(
              scope.organizationId,
              scope.socialAccountId,
              { since: scope.since, until: scope.until, platform: scope.platform, signal },
            ),
            staleTime: 0,
          }).catch(() => {}),
          queryClient.invalidateQueries({ queryKey: contentSnapshotKey(scope) }),
        ]);
        return;
      }

      if (response.status === 200) {
        await Promise.all([
          queryClient.fetchQuery({
            queryKey: key,
            queryFn: ({ signal }) => insightsService.getAccountSnapshot(
              scope.organizationId,
              scope.socialAccountId,
              { since: scope.since, until: scope.until, platform: scope.platform, signal },
            ),
            staleTime: 0,
          }).catch(() => {}),
          queryClient.invalidateQueries({ queryKey: contentSnapshotKey(scope) }),
        ]);
      }
    },
  });

  const organizations = Array.isArray(organizationsQuery.data) ? organizationsQuery.data : [];
  const accounts = platform
    ? supportedAccounts.filter((account) => String(account.platform).toLowerCase() === platform)
    : supportedAccounts;
  function handleOrganizationChange(value) {
    setOrganizationId(value);
    setPlatform("");
    setAccountId("");
    setContentPage(1);
  }

  function handleDurationChange(value) {
    setDuration(value);
    setContentPage(1);
  }

  function handlePlatformChange(value) {
    setPlatform(value);
    setAccountId("");
    const availableDurations = value === "facebook" ? ["7D", "28D"] : ["7D", "30D"];
    if (!availableDurations.includes(duration)) {
      setDuration(value === "facebook" ? "7D" : "30D");
    }
    setContentPage(1);
  }

  function handleAccountChange(value) {
    setAccountId(value);
    const nextAccount = supportedAccounts.find((account) => String(account.id) === value);
    const nextPlatform = String(nextAccount?.platform || platform).toLowerCase();
    const availableDurations = nextPlatform === "facebook" ? ["7D", "28D"] : ["7D", "30D"];
    if (!availableDurations.includes(duration)) {
      setDuration(nextPlatform === "facebook" ? "7D" : "30D");
    }
    setContentPage(1);
  }

  function handleNextPage() {
    const pagination = contentSnapshotQuery.data?.content_performance?.pagination;
    if (pagination?.has_next) setContentPage((page) => page + 1);
  }

  function handlePreviousPage() {
    const pagination = contentSnapshotQuery.data?.content_performance?.pagination;
    if (pagination?.has_previous) setContentPage((page) => Math.max(1, page - 1));
  }

  const accountData = accountSnapshotQuery.data;
  const contentData = contentSnapshotQuery.data;
  const accountOverview = accountData?.account_overview;
  const rawMetrics = accountOverview?.metrics || {};
  const metricKeys = ["reach", "engagement", "followers", "views"];
  const metrics = Object.fromEntries(metricKeys.map((key) => [
    key,
    rawMetrics[key] || {
      value: null,
      availability: "unavailable",
      reason: accountOverview?.reason || "metric_not_recorded",
    },
  ]));
  const accountSync = accountData?.freshness?.sync;
  const contentSync = contentData?.freshness?.sync;
  const activeAccountStageStatus = activeSync?.account_status;
  const activeContentStageStatus = activeSync?.content_status;
  const accountStageStatus = ACTIVE_SYNC_STATUSES.includes(activeAccountStageStatus)
    || activeAccountStageStatus === "complete"
    ? activeAccountStageStatus
    : accountSync?.account_status || accountSync?.status;
  const contentStageStatus = ACTIVE_SYNC_STATUSES.includes(activeContentStageStatus)
    || activeContentStageStatus === "complete"
    ? activeContentStageStatus
    : contentSync?.content_status || contentSync?.status;
  const accountSnapshotFreshness = accountData?.freshness?.account_snapshot;
  const contentFreshness = contentData?.freshness?.content;
  const accountSnapshotRange = formatSnapshotRange(accountSnapshotFreshness?.since, accountSnapshotFreshness?.until);
  const contentSnapshotRange = formatSnapshotRange(contentFreshness?.since, contentFreshness?.until);
  const accountLoading = selected && accountSnapshotQuery.isLoading;
  const contentLoading = selected && contentSnapshotQuery.isLoading;
  const pagination = contentData?.content_performance?.pagination;
  const overallSyncStatus = accountSyncStatus;
  function syncSummary(label, sync, updatedAt, status = sync?.status, includeProgress = false, moreContentAvailable = false, snapshotRange = "", progress = sync?.progress) {
    if (!status) return null;
    const processed = progress?.processed;
    const total = progress?.total;
    const hasProcessed = typeof processed === "number" && Number.isFinite(processed) && processed >= 0;
    const hasTotal = typeof total === "number" && Number.isFinite(total) && total > 0;
    const showActiveContentProgress = includeProgress && ACTIVE_SYNC_STATUSES.includes(status);
    const progressLabel = showActiveContentProgress && hasProcessed
      ? hasTotal
        ? ` · ${processed} / ${total} posts fetched · ${Math.round(Math.min(100, Math.max(0, (processed / total) * 100)))}%${moreContentAvailable ? " · More content available" : ""}`
        : ` · ${processed} ${processed === 1 ? "post" : "posts"} fetched · total being determined`
      : "";
    const rangeLabel = snapshotRange ? ` · ${snapshotRange}` : "";
    const updatedLabel = updatedAt ? ` · Updated ${dayjs(updatedAt).format("MMM D, YYYY h:mm A")}` : "";
    return `${label}: ${status}${rangeLabel}${progressLabel}${updatedLabel}`;
  }

  const accountSyncSeverity = ["failed", "partial"].includes(accountStageStatus) ? "warning" : "info";
  const contentSyncSeverity = ["failed", "partial"].includes(contentStageStatus) ? "warning" : "info";
  const isSyncActive = isActiveSyncRunning(activeSync);
  const isFinalizingSync = Boolean(currentScopeKey && (
    finalizingSyncScopes.has(currentScopeKey)
    || (activeSyncScopeKeys.has(currentScopeKey) && !isSyncActive)
  ));
  const isRefreshingInsights = isSyncActive || isFinalizingSync;

  useEffect(() => {
    if (!currentScopeKey) return;
    if (isActiveSyncRunning(activeSync)) {
      if (!activeSyncScopes.current.has(currentScopeKey)) {
        activeSyncScopes.current.add(currentScopeKey);
        setActiveSyncScopeKeys((current) => new Set(current).add(currentScopeKey));
      }
      return;
    }
    if (!activeSyncScopes.current.has(currentScopeKey)
      || finalizingSyncScopesRef.current.has(currentScopeKey)) return;

    const completedScopeKey = currentScopeKey;
    finalizingSyncScopesRef.current.add(completedScopeKey);
    setFinalizingSyncScopes((current) => new Set(current).add(completedScopeKey));
    void Promise.all([
      queryClient.invalidateQueries({
        queryKey: accountSnapshotKey(currentScope),
        refetchType: "active",
      }),
      queryClient.invalidateQueries({
        queryKey: contentSnapshotKey(currentScope),
        refetchType: "active",
      }),
    ]).finally(() => {
      activeSyncScopes.current.delete(completedScopeKey);
      finalizingSyncScopesRef.current.delete(completedScopeKey);
      setActiveSyncScopeKeys((current) => {
        const next = new Set(current);
        next.delete(completedScopeKey);
        return next;
      });
      setFinalizingSyncScopes((current) => {
        const next = new Set(current);
        next.delete(completedScopeKey);
        return next;
      });
    });
  }, [activeSync, currentScope, currentScopeKey, queryClient]);

  const activeStageIssues = [
    ["Account", activeAccountStageStatus],
    ["Content", activeContentStageStatus],
  ].filter(([, status]) => ["failed", "partial"].includes(status));

  const mutationScopeKey = syncMutation.variables ? scopeKey(syncMutation.variables) : "";
  const syncPendingForCurrentScope = syncMutation.isPending && mutationScopeKey === currentScopeKey;
  const syncErrorForCurrentScope = syncMutation.isError && mutationScopeKey === currentScopeKey;
  const accountSnapshotMissing = accountOverview?.availability === "not_ready"
    && accountOverview?.reason === "snapshot_not_found";
  const canRequestSync = selected && ["instagram", "facebook"].includes(selectedPlatform) && !isRefreshingInsights
    && (accountSnapshotMissing || ["complete", "partial", "failed"].includes(overallSyncStatus));

  function handleSyncInsights() {
    if (currentScope && ["instagram", "facebook"].includes(selectedPlatform) && !syncPendingForCurrentScope) {
      syncMutation.mutate({
        ...currentScope,
        forceRefresh: overallSyncStatus === "complete",
      });
    }
  }

  return (
    <Stack spacing={2.5}>
      <InsightsHeader
        organizations={organizations}
        organizationId={organizationId}
        accounts={supportedAccounts}
        duration={duration}
        platform={platform}
        accountId={accountId}
        organizationsLoading={organizationsQuery.isLoading}
        exportEnabled={Boolean(currentScope && ["instagram", "facebook"].includes(selectedPlatform))}
        onExportSelect={setExportMode}
        onOrganizationChange={handleOrganizationChange}
        onDurationChange={handleDurationChange}
        onPlatformChange={handlePlatformChange}
        onAccountChange={handleAccountChange}
      />

      <InsightsExportDialog
        open={Boolean(exportMode)}
        mode={exportMode || "current"}
        scope={currentScope}
        organization={organizations.find((item) => String(item.id) === organizationId)}
        account={selectedAccount}
        onClose={() => setExportMode("")}
      />

      {organizationsQuery.isError && (
        <Alert
          severity="error"
          action={<Button color="inherit" size="small" onClick={() => organizationsQuery.refetch()}>Retry</Button>}
        >
          Could not load accessible organizations. Please try again.
        </Alert>
      )}
      {organizationsQuery.isSuccess && !organizations.length && (
        <Alert severity="info">No accessible organizations are available for Insights.</Alert>
      )}
      {organizationId && accountsQuery.isError && (
        <Alert
          severity="error"
          action={<Button color="inherit" size="small" onClick={() => accountsQuery.refetch()}>Retry</Button>}
        >
          Could not load connected accounts for this organization.
        </Alert>
      )}
      {organizationId && accountsQuery.isSuccess && !supportedAccounts.length && (
        <Alert severity="info">No connected Instagram or Facebook accounts are available for this organization.</Alert>
      )}
      {organizationId && platform && accountsQuery.isSuccess && supportedAccounts.length > 0 && !accounts.length && (
        <Alert severity="info">No connected {platform[0].toUpperCase() + platform.slice(1)} accounts are available for this organization.</Alert>
      )}
      {selected && accountSnapshotQuery.isError && (
        <Alert
          severity="error"
          action={<Button color="inherit" size="small" onClick={() => accountSnapshotQuery.refetch()}>Retry</Button>}
        >
          Could not load account Insights for the selected account. Please try again.
        </Alert>
      )}
      {selected && contentSnapshotQuery.isError && (
        <Alert
          severity="error"
          action={<Button color="inherit" size="small" onClick={() => contentSnapshotQuery.refetch()}>Retry</Button>}
        >
          Could not load content Insights for the selected account. Please try again.
        </Alert>
      )}
      {selected && accountSync && (
        <Alert severity={accountSyncSeverity}>
      {syncSummary(
        "Account snapshot",
        accountSync,
        accountSnapshotFreshness?.updated_at || accountSnapshotFreshness?.fetched_at,
        accountStageStatus,
        false,
        false,
        accountSnapshotRange,
      )}
        </Alert>
      )}
      {selected && ["instagram", "facebook"].includes(selectedPlatform) && overallSyncStatus === "complete" && !accountSnapshotMissing && (
        <Alert
          severity="info"
          action={canRequestSync && !syncErrorForCurrentScope && (
            <Button color="inherit" size="small" onClick={handleSyncInsights} disabled={syncPendingForCurrentScope}>
              {syncPendingForCurrentScope ? "Starting…" : "Refresh Insights"}
            </Button>
          )}
        >
          Refresh to fetch the latest available Insights. The timestamp above is the last persisted snapshot update.
        </Alert>
      )}
      {selected && contentSync && (
        <Alert severity={contentSyncSeverity}>
          <Stack spacing={1} sx={{ width: "100%" }}>
            <Typography component="span" sx={{ color: "inherit", fontSize: "inherit" }}>
              {syncSummary(
                "Content snapshot",
                contentSync,
                contentFreshness?.updated_at || contentFreshness?.completed_at || contentFreshness?.newest_fetched_at,
                contentStageStatus,
                true,
                contentStageStatus === "partial" && contentSync.more_content_available === true,
                contentSnapshotRange,
                activeSync?.progress,
              )}
            </Typography>
            {ACTIVE_SYNC_STATUSES.includes(contentStageStatus)
              && typeof activeSync?.progress?.processed === "number"
              && Number.isFinite(activeSync.progress.processed)
              && activeSync.progress.processed >= 0
              && typeof activeSync?.progress?.total === "number"
              && Number.isFinite(activeSync.progress.total)
              && activeSync.progress.total > 0 ? (
              <LinearProgress
                variant="determinate"
                value={Math.min(100, Math.max(0, (activeSync.progress.processed / activeSync.progress.total) * 100))}
                sx={{ height: 5, borderRadius: 4, bgcolor: "rgba(25, 118, 210, 0.14)", "& .MuiLinearProgress-bar": { borderRadius: 4 } }}
              />
            ) : ACTIVE_SYNC_STATUSES.includes(contentStageStatus) ? (
              <LinearProgress
                variant="indeterminate"
                sx={{ height: 5, borderRadius: 4, bgcolor: "rgba(25, 118, 210, 0.14)", "& .MuiLinearProgress-bar": { borderRadius: 4 } }}
              />
            ) : null}
          </Stack>
        </Alert>
      )}
      {selected && activeStageIssues.length > 0 && (
        <Alert severity="warning">
          Latest {activeStageIssues.map(([stage, status]) => `${stage.toLowerCase()} refresh ${status}`).join(" and ")}.
          Previously published snapshots remain visible.
        </Alert>
      )}
      {selected && accountSnapshotMissing && (
        <Alert
          severity="info"
          action={canRequestSync && !["partial", "failed"].includes(overallSyncStatus) && !syncErrorForCurrentScope && (
            <Button color="inherit" size="small" onClick={handleSyncInsights} disabled={syncPendingForCurrentScope}>
              {syncPendingForCurrentScope ? "Starting…" : "Sync Insights"}
            </Button>
          )}
        >
          No account snapshot is available for this duration yet.
        </Alert>
      )}
      {selected && isRefreshingInsights && (
        <Alert severity="info">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <CircularProgress size={16} />
            <span>
              {isFinalizingSync
                ? "Loading the published snapshot…"
                : overallSyncStatus === "queued"
                ? "Insights sync queued…"
                : accountSnapshotFreshness?.exists
                  ? "Refreshing Insights… Showing the last saved snapshot while this refresh runs."
                  : "Syncing Insights…"}
            </span>
          </Box>
        </Alert>
      )}
      {selected && overallSyncStatus === "partial" && (
        <Alert severity="warning" action={canRequestSync && (
            <Button color="inherit" size="small" onClick={handleSyncInsights} disabled={syncPendingForCurrentScope}>
            {syncPendingForCurrentScope ? "Starting…" : "Retry Sync"}
          </Button>
        )}>
          Insights sync is partial. Available saved metrics and content are shown where present.
        </Alert>
      )}
      {selected && overallSyncStatus === "failed" && (
        <Alert severity="warning" action={canRequestSync && (
            <Button color="inherit" size="small" onClick={handleSyncInsights} disabled={syncPendingForCurrentScope}>
            {syncPendingForCurrentScope ? "Starting…" : "Retry Sync"}
          </Button>
        )}>
          Insights sync failed. Any saved metrics and content remain available; you can retry manually.
        </Alert>
      )}
      {selected && syncErrorForCurrentScope && (
        <Alert severity="error" action={canRequestSync && (
            <Button color="inherit" size="small" onClick={handleSyncInsights} disabled={syncPendingForCurrentScope}>
            Retry Sync
          </Button>
        )}>
          Could not start the Insights sync. Please try again.
        </Alert>
      )}

      <Stack spacing={2.5}>
        <InsightsStats metrics={metrics} loading={accountLoading} selected={selected && !accountSnapshotQuery.isError} />
        <PostPerformanceCard
          organizationId={organizationId}
          socialAccountId={accountId}
          platform={selectedPlatform}
          duration={duration}
          since={dateRange.since}
          until={dateRange.until}
          selected={selected}
        />
        <ContentPerformanceCard
          content={contentData?.content_performance}
          account={accountData?.account || selectedAccount}
          loading={contentLoading}
          selected={selected && !contentSnapshotQuery.isError}
          pagination={pagination}
          pageNumber={pagination?.page || contentPage}
          onNext={handleNextPage}
          onPrevious={handlePreviousPage}
        />
      </Stack>

      {selected && (accountSnapshotQuery.isFetching || contentSnapshotQuery.isFetching)
        && !accountSnapshotQuery.isLoading && !contentSnapshotQuery.isLoading && (
        <Box sx={{ position: "fixed", right: 22, bottom: 20, bgcolor: "#fff", border: "1px solid #E3EAF4", borderRadius: 5, p: 0.7, display: "flex", alignItems: "center", gap: 1, boxShadow: "0 5px 18px #1F315018" }}>
          <CircularProgress size={16} />
          <Typography sx={{ color: "#637997", fontSize: 12 }}>Updating Insights…</Typography>
        </Box>
      )}
    </Stack>
  );
}
