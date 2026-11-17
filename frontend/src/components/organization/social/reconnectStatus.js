export function shouldReconnectPage(account) {
  return account?.pageNeedsReconnect === true;
}

export function getParentReconnectGroups(accounts) {
  if (!Array.isArray(accounts)) {
    return [];
  }

  const groups = new Map();

  accounts.forEach((account, index) => {
    if (account?.platform !== "facebook" || account.parentNeedsReconnect !== true) {
      return;
    }

    const connectionId = account.parentConnectionId;
    const key = connectionId || `account:${account.id ?? index}`;

    if (!groups.has(key)) {
      groups.set(key, {
        key,
        connectionId,
        parentUserCredentialStatus: account.parentUserCredentialStatus || null,
        accounts: [],
      });
    }

    groups.get(key).accounts.push(account);
  });

  return Array.from(groups.values());
}
