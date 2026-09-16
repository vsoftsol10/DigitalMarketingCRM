// // ============================================================
// // SOCIAL ACCOUNT MAPPER
// // Backend API response → Frontend model
// // ============================================================

// export function mapSocialAccount(account) {
//   if (!account) {
//     return null;
//   }

//   return {
//     id: account.id,
//     platform: account.platform,

//     pageName: account.page_name || "",
//     username: account.username || "",

//     profileImage: account.profile_image || "",

//     connected: Boolean(account.connected),
//     valid: Boolean(account.valid),

//     lastSync: account.last_sync || null,
//   };
// }

// export function mapSocialAccounts(accounts) {
//   if (!Array.isArray(accounts)) {
//     return [];
//   }

//   return accounts
//     .map(mapSocialAccount)
//     .filter(Boolean);
// }

// ============================================================
// SOCIAL ACCOUNT MAPPER
// Backend API response → Frontend model
// ============================================================

export function mapSocialAccount(account) {
  if (!account) {
    return null;
  }

  return {
    // ========================================================
    // IDENTITY
    // ========================================================

    id: account.id || null,

    platform: account.platform || "",

    pageName: account.page_name || "",
    username: account.username || "",

    profileImage: account.profile_image || "",

    // ========================================================
    // EXISTING ACCOUNT STATE
    // ========================================================
    //
    // Keep these fields for backward compatibility.
    //
    // IMPORTANT:
    // Only explicit backend true is treated as true.
    // Missing/undefined values must NOT become true.
    //

    connected: account.connected === true,

    valid: account.valid === true,

    lastSync: account.last_sync || null,

    // ========================================================
    // LIFECYCLE STATE
    // ========================================================
    //
    // These values come directly from the backend lifecycle
    // contract.
    //

    connectionStatus: account.connection_status || null,

    credentialStatus: account.credential_status || null,

    lastVerifiedAt: account.last_verified_at || null,

    needsReconnect: account.needs_reconnect === true,
  };
}

// ============================================================
// SOCIAL ACCOUNTS MAPPER
// ============================================================

export function mapSocialAccounts(accounts) {
  if (!Array.isArray(accounts)) {
    return [];
  }

  return accounts.map(mapSocialAccount).filter(Boolean);
}
