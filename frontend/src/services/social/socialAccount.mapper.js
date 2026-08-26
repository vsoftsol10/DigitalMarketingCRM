// ============================================================
// SOCIAL ACCOUNT MAPPER
// Backend API response → Frontend model
// ============================================================

export function mapSocialAccount(account) {
  if (!account) {
    return null;
  }

  return {
    id: account.id,
    platform: account.platform,

    pageName: account.page_name || "",
    username: account.username || "",

    profileImage: account.profile_image || "",

    connected: Boolean(account.connected),
    valid: Boolean(account.valid),

    lastSync: account.last_sync || null,
  };
}

export function mapSocialAccounts(accounts) {
  if (!Array.isArray(accounts)) {
    return [];
  }

  return accounts
    .map(mapSocialAccount)
    .filter(Boolean);
}