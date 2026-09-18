export function buildCreatePostPayload(data, accounts = []) {
  const media = Array.isArray(data.media) ? data.media : [];

  const socialAccountIds = Array.isArray(data.social_account_ids)
    ? data.social_account_ids.filter(Boolean)
    : [];

  const platformContentTypes =
    data.platform_content_types &&
    typeof data.platform_content_types === "object"
      ? data.platform_content_types
      : {};

  const accountById = new Map(
    accounts.map((account) => [account?.id, account]),
  );

  return {
    // The organization is intentionally omitted: the backend resolves it from
    // the organization-scoped endpoint URL.
    targets: socialAccountIds.map((socialAccountId) => {
      const platform = accountById.get(socialAccountId)?.platform || "";

      return {
        social_account: socialAccountId,
        content_type: platformContentTypes[platform] || "",
      };
    }),

    // ==========================================================
    // MEDIA
    // ==========================================================

    media: media.map((item) => ({
      file: item.file,
      media_type: String(item.type || "").toUpperCase(),
    })),

    // ==========================================================
    // CAPTION
    // ==========================================================

    caption: data.caption,

    publish_type: data.publish_type,
    publish_date: data.publish_type === "SCHEDULE" ? data.publish_date : null,
    publish_time: data.publish_type === "SCHEDULE" ? data.publish_time : null,
    timezone: data.timezone,
  };
}
