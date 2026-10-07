import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import {
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  MenuItem,
  Select,
  Skeleton,
  Typography,
} from "@mui/material";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import insightsService from "../../services/insights.service";
import formatCompactNumber from "../../utils/formatters/formatCompactNumber";

const PAGE_FETCH_CONCURRENCY = 3;
const PAGE_CACHE_STALE_TIME = 60_000;
const CHART_CACHE_STALE_TIME = 60_000;

const METRICS_BY_PLATFORM = {
  instagram: [
    { key: "reach", label: "Reach" },
    { key: "engagement", label: "Engagement" },
    { key: "likes_reactions", label: "Likes / Reactions" },
    { key: "comments", label: "Comments" },
    { key: "shares", label: "Shares" },
  ],
  facebook: [
    { key: "reach", label: "Reach" },
    { key: "views", label: "Views" },
    { key: "likes_reactions", label: "Reactions" },
    { key: "comments", label: "Comments" },
    { key: "clicks", label: "Clicks" },
  ],
};

function contentScopeKey({ organizationId, socialAccountId, platform, duration }) {
  return ["insights-content-snapshot", organizationId, socialAccountId, duration, platform];
}

function contentPageKey(scope, page) {
  return [...contentScopeKey(scope), page];
}

async function fetchContentPage(queryClient, scope, page) {
  return queryClient.fetchQuery({
    queryKey: contentPageKey(scope, page),
    queryFn: ({ signal }) => insightsService.getContentSnapshot(
      scope.organizationId,
      scope.socialAccountId,
      {
        since: scope.since,
        until: scope.until,
        platform: scope.platform,
        page,
        signal,
      },
    ),
    staleTime: PAGE_CACHE_STALE_TIME,
    retry: false,
  });
}

async function fetchAllContentPages(queryClient, scope) {
  const firstPage = await fetchContentPage(queryClient, scope, 1);
  const firstResults = firstPage?.content_performance?.results;
  const pagination = firstPage?.content_performance?.pagination;
  const totalPages = Number(pagination?.total_pages);

  if (!Array.isArray(firstResults)) {
    throw new Error("Content snapshot response is missing its results.");
  }

  if (!Number.isInteger(totalPages) || totalPages < 0) {
    throw new Error("Content snapshot response is missing pagination details.");
  }

  if (totalPages === 0) {
    const totalItems = Number(pagination?.total_items);
    if (firstResults.length || pagination?.has_next || (Number.isInteger(totalItems) && totalItems !== 0)) {
      throw new Error("Content snapshot pagination details are inconsistent.");
    }
    return { items: [], freshness: firstPage?.freshness?.content };
  }

  const allResults = [...firstResults];
  const pagesToLoad = Array.from({ length: Math.max(0, totalPages - 1) }, (_, index) => index + 2);
  let nextPageIndex = 0;
  let pageLoadError = null;

  async function loadPages() {
    while (!pageLoadError && nextPageIndex < pagesToLoad.length) {
      const pageIndex = nextPageIndex;
      nextPageIndex += 1;
      try {
        const page = await fetchContentPage(queryClient, scope, pagesToLoad[pageIndex]);
        const results = page?.content_performance?.results;
        if (!Array.isArray(results)) {
          throw new Error("A content snapshot page is missing its results.");
        }
        allResults.push(...results);
      } catch (error) {
        pageLoadError = error;
      }
    }
  }

  const workerCount = Math.min(PAGE_FETCH_CONCURRENCY, pagesToLoad.length);
  await Promise.all(Array.from({ length: workerCount }, () => loadPages()));
  if (pageLoadError) throw pageLoadError;

  const uniqueResults = [];
  const seenMediaIds = new Set();
  allResults.forEach((item) => {
    const mediaId = item.provider_media_id ?? item.id;
    if (mediaId == null) {
      uniqueResults.push(item);
      return;
    }
    const key = String(mediaId);
    if (seenMediaIds.has(key)) return;
    seenMediaIds.add(key);
    uniqueResults.push(item);
  });

  const totalItems = Number(pagination?.total_items);
  if (Number.isInteger(totalItems) && totalItems >= 0 && uniqueResults.length !== totalItems) {
    throw new Error("The content snapshot pages do not match the reported item count.");
  }

  return { items: uniqueResults, freshness: firstPage?.freshness?.content };
}

function formatSnapshotRange(since, until) {
  if (!since || !until) return "";
  const start = dayjs(since);
  const end = dayjs(until);
  if (!start.isValid() || !end.isValid()) return "";
  const startLabel = start.format("MMM D, YYYY");
  const endLabel = end.format("MMM D, YYYY");
  return startLabel === endLabel ? startLabel : `${startLabel} – ${endLabel}`;
}

function metricForPost(post, metricKey, platform) {
  if (metricKey === "likes_reactions") {
    return String(platform).toLowerCase() === "facebook"
      ? post.metrics?.reactions
      : post.metrics?.likes;
  }
  return post.metrics?.[metricKey];
}

function aggregatePostsByDay(posts, { since, until, platform }) {
  const daily = new Map();
  const normalizedPlatform = String(platform).toLowerCase();
  const metrics = METRICS_BY_PLATFORM[normalizedPlatform] || METRICS_BY_PLATFORM.instagram;
  const metricKeys = metrics.map(({ key }) => key);

  posts.forEach((post) => {
    if (!post.published_at) return;
    const date = dayjs(post.published_at);
    if (!date.isValid()) return;
    const dateKey = date.format("YYYY-MM-DD");
    if (dateKey < since || dateKey > until) return;

    const bucket = daily.get(dateKey) || {
      posts: 0,
      metrics: Object.fromEntries(metricKeys.map((key) => [key, { values: 0, total: 0 }])),
    };
    bucket.posts += 1;
    metricKeys.forEach((key) => {
      const metric = metricForPost(post, key, platform);
      if (metric?.availability === "available" && typeof metric.value === "number" && Number.isFinite(metric.value)) {
        bucket.metrics[key].values += 1;
        bucket.metrics[key].total += metric.value;
      }
    });
    daily.set(dateKey, bucket);
  });

  const days = [];
  let current = dayjs(since);
  const end = dayjs(until);
  while (current.isValid() && !current.isAfter(end, "day")) {
    const date = current.format("YYYY-MM-DD");
    const bucket = daily.get(date);
    const metrics = Object.fromEntries(metricKeys.map((key) => [
      key,
      !bucket ? 0 : bucket.metrics[key].values === bucket.posts ? bucket.metrics[key].total : null,
    ]));
    days.push({
      date,
      label: current.format("MMM D"),
      posts: bucket?.posts || 0,
      metrics,
    });
    current = current.add(1, "day");
  }
  return days;
}

const TOOLTIP_METRICS_BY_PLATFORM = {
  instagram: [
    { key: "reach", label: "Reach" },
    { key: "engagement", label: "Engagement" },
    { key: "likes_reactions", label: "Likes / Reactions" },
    { key: "comments", label: "Comments" },
    { key: "shares", label: "Shares" },
  ],
  facebook: [
    { key: "reach", label: "Reach" },
    { key: "views", label: "Views" },
    { key: "likes_reactions", label: "Reactions" },
    { key: "comments", label: "Comments" },
    { key: "clicks", label: "Clicks" },
  ],
};

function DailyMetricTooltip({ active, payload, metricKey, platform }) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;
  const normalizedPlatform = String(platform).toLowerCase();
  const tooltipMetrics = TOOLTIP_METRICS_BY_PLATFORM[normalizedPlatform]
    || TOOLTIP_METRICS_BY_PLATFORM.instagram;

  return (
    <Box sx={{ minWidth: 210, px: 1.75, py: 1.35, border: "1px solid #E7ECF4", borderRadius: 2, bgcolor: "#fff", boxShadow: "0 8px 24px rgba(25, 42, 70, 0.12)" }}>
      <Typography sx={{ color: "#26354B", fontSize: 12.5, fontWeight: 700, mb: 0.8 }}>
        {dayjs(point.date).format("dddd, MMM D")}
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 0.35 }}>
        <TooltipMetricRow label="Post Published" value={point.posts} />
        {tooltipMetrics.map((metric) => (
          <TooltipMetricRow
            key={metric.key}
            label={metric.label}
            value={point.metrics?.[metric.key]}
            selected={metricKey === metric.key}
          />
        ))}
      </Box>
    </Box>
  );
}

function TooltipMetricRow({ label, value, selected = false }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
      <Typography sx={{ color: "#8292AA", fontSize: 12, whiteSpace: "nowrap" }}>{label}</Typography>
      <Typography sx={{ color: selected && value != null ? "#3563F5" : "#4B5563", fontSize: 12, fontWeight: selected ? 700 : 600, textAlign: "right" }}>
        {value == null ? "Unavailable" : formatCompactNumber(value)}
        </Typography>
    </Box>
  );
}

function ChartMessage({ children, action }) {
  return (
    <Box sx={{ height: { xs: 260, sm: 320 }, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", px: 2 }}>
      <Box>
        <Typography sx={{ color: "#52647C", fontSize: 14, fontWeight: 600 }}>{children}</Typography>
        {action}
      </Box>
    </Box>
  );
}

export default function PostPerformanceCard({
  organizationId,
  socialAccountId,
  platform,
  duration,
  since,
  until,
  selected,
}) {
  const queryClient = useQueryClient();
  const normalizedPlatform = String(platform).toLowerCase();
  const metrics = METRICS_BY_PLATFORM[normalizedPlatform] || METRICS_BY_PLATFORM.instagram;
  const [metricSelection, setMetricSelection] = useState({
    platform: normalizedPlatform,
    metricKey: "reach",
  });
  const selectionIsSupported = metrics.some((metric) => metric.key === metricSelection.metricKey);
  const activeMetricKey = selectionIsSupported ? metricSelection.metricKey : "reach";
  if (metricSelection.platform !== normalizedPlatform) {
    setMetricSelection({
      platform: normalizedPlatform,
      metricKey: selectionIsSupported ? metricSelection.metricKey : "reach",
    });
  }
  const scope = useMemo(() => ({ organizationId, socialAccountId, platform, duration, since, until }), [
    organizationId,
    duration,
    platform,
    since,
    socialAccountId,
    until,
  ]);
  const contentQuery = useQuery({
    queryKey: [...contentScopeKey(scope), "post-performance"],
    queryFn: () => fetchAllContentPages(queryClient, scope),
    enabled: selected && Boolean(organizationId && socialAccountId && platform && since && until),
    staleTime: CHART_CACHE_STALE_TIME,
    gcTime: 30 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
    placeholderData: undefined,
  });
  const selectedMetric = metrics.find((metric) => metric.key === activeMetricKey) || metrics[0];
  const snapshotSince = contentQuery.data?.freshness?.since || since;
  const snapshotUntil = contentQuery.data?.freshness?.until || until;
  const snapshotRange = formatSnapshotRange(snapshotSince, snapshotUntil);
  const dailyMetrics = useMemo(() => {
    if (!contentQuery.data) return [];
    return aggregatePostsByDay(contentQuery.data.items, {
      since: snapshotSince,
      until: snapshotUntil,
      platform,
    });
  }, [contentQuery.data, platform, snapshotSince, snapshotUntil]);
  const chartData = useMemo(() => dailyMetrics.map((point) => ({
    ...point,
    value: point.metrics[activeMetricKey],
  })), [activeMetricKey, dailyMetrics]);
  const hasPosts = chartData.some((point) => point.posts > 0);
  const hasAvailableMetric = chartData.some((point) => point.posts > 0 && typeof point.value === "number");

  return (
    <Card elevation={0} sx={{ width: "100%", minWidth: 0, border: "1px solid #E5EAF2", borderRadius: "18px", bgcolor: "#fff", boxShadow: "0 3px 12px rgba(22, 42, 78, 0.045)" }}>
      <CardContent sx={{ p: { xs: 2, sm: 2.5, lg: 3 }, "&:last-child": { pb: { xs: 2, sm: 2.5, lg: 3 } } }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: { xs: "flex-start", sm: "center" }, flexDirection: { xs: "column", sm: "row" }, gap: 1.5, mb: 1.5 }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ color: "#252B38", fontSize: 20, lineHeight: 1.3, fontWeight: 700 }}>Post Performance</Typography>
            <Typography sx={{ mt: 0.5, color: "#718096", fontSize: 14 }}>
              Daily performance of posts published{snapshotRange ? ` during ${snapshotRange}` : " during the saved snapshot period"}.
            </Typography>
          </Box>
          <FormControl size="small" sx={{ width: { xs: "100%", sm: 180 }, flexShrink: 0 }}>
            <Select
              value={activeMetricKey}
              onChange={(event) => setMetricSelection({
                platform: normalizedPlatform,
                metricKey: event.target.value,
              })}
              inputProps={{ "aria-label": "Post performance metric" }}
              sx={{ height: 50, borderRadius: "14px", color: "#344054", fontSize: 14, "& .MuiOutlinedInput-notchedOutline": { borderColor: "#D7DEE8" } }}
            >
              {metrics.map((metric) => <MenuItem key={metric.key} value={metric.key}>{metric.label}</MenuItem>)}
            </Select>
          </FormControl>
        </Box>

        {contentQuery.isLoading ? (
          <Box sx={{ height: { xs: 260, sm: 320 } }}>
            <Skeleton variant="rounded" width="100%" height="100%" sx={{ borderRadius: 3 }} />
          </Box>
        ) : contentQuery.isError ? (
          <ChartMessage action={(
            <Button size="small" onClick={() => contentQuery.refetch()} sx={{ mt: 1, textTransform: "none" }}>
              Retry chart data
            </Button>
          )}>
            Could not load all post performance data for this period.
          </ChartMessage>
        ) : !selected ? (
          <ChartMessage>Select an account to view post performance.</ChartMessage>
        ) : !hasPosts ? (
          <ChartMessage>No posts were found in this published snapshot.</ChartMessage>
        ) : !hasAvailableMetric ? (
          <ChartMessage>{selectedMetric.label} data is unavailable for the posts in this published snapshot.</ChartMessage>
        ) : (
          <Box sx={{ width: "100%", height: { xs: 260, sm: 320 }, minWidth: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 20, right: 14, left: -12, bottom: 8 }}>
                <defs>
                  <linearGradient id="post-performance-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3563F5" stopOpacity={0.14} />
                    <stop offset="100%" stopColor="#3563F5" stopOpacity={0.015} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#E9EEF5" vertical={false} />
                <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#8292AA" }} minTickGap={22} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#8292AA" }} tickFormatter={formatCompactNumber} width={48} allowDecimals={false} />
                <Tooltip filterNull={false} content={<DailyMetricTooltip metricKey={activeMetricKey} platform={platform} />} />
                <Area
                  type="linear"
                  dataKey="value"
                  name={selectedMetric.label}
                  stroke="#3563F5"
                  strokeWidth={3}
                  fill="url(#post-performance-fill)"
                  connectNulls={false}
                  activeDot={{ r: 4, fill: "#3563F5", stroke: "#fff", strokeWidth: 2 }}
                  dot={false}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
