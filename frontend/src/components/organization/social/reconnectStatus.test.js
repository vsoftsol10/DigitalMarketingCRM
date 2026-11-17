import assert from "node:assert/strict";
import test from "node:test";

import { mapSocialAccount } from "../../../services/social/socialAccount.mapper.js";
import {
  getParentReconnectGroups,
  shouldReconnectPage,
} from "./reconnectStatus.js";

function account({
  id,
  connectionId,
  parentStatus = "active",
  pageStatus = "active",
  parentNeedsReconnect = false,
  pageNeedsReconnect = false,
  connected = true,
  valid = true,
  platform = "facebook",
}) {
  return mapSocialAccount({
    id,
    platform,
    page_name: id,
    connected,
    valid,
    credential_status: pageStatus,
    parent_user_credential_status: parentStatus,
    parent_connection_id: connectionId,
    needs_reconnect: parentNeedsReconnect || pageNeedsReconnect,
    parent_needs_reconnect: parentNeedsReconnect,
    page_needs_reconnect: pageNeedsReconnect,
  });
}

test("invalid parent with active Page shows parent notice without Page reconnect action", () => {
  const page = account({
    id: "page-active",
    connectionId: "connection-invalid-parent",
    parentStatus: "invalid",
    parentNeedsReconnect: true,
  });

  assert.equal(page.connected, true);
  assert.equal(page.credentialStatus, "active");
  assert.equal(shouldReconnectPage(page), false);
  assert.equal(getParentReconnectGroups([page]).length, 1);
});

test("active parent with invalid Page shows only the Page reconnect action", () => {
  const page = account({
    id: "page-invalid",
    connectionId: "connection-active-parent",
    pageStatus: "invalid",
    pageNeedsReconnect: true,
  });

  assert.equal(page.parentUserCredentialStatus, "active");
  assert.equal(shouldReconnectPage(page), true);
  assert.equal(getParentReconnectGroups([page]).length, 0);
});

test("active parent and Page show neither reconnect state", () => {
  const page = account({ id: "page-healthy", connectionId: "connection-healthy" });

  assert.equal(shouldReconnectPage(page), false);
  assert.equal(getParentReconnectGroups([page]).length, 0);
});

test("both invalid states keep parent notice and Page reconnect distinct", () => {
  const page = account({
    id: "page-and-parent-invalid",
    connectionId: "connection-both-invalid",
    parentStatus: "invalid",
    pageStatus: "invalid",
    parentNeedsReconnect: true,
    pageNeedsReconnect: true,
    connected: false,
    valid: false,
  });

  assert.equal(shouldReconnectPage(page), true);
  assert.equal(getParentReconnectGroups([page]).length, 1);
});

test("Pages sharing one invalid parent produce one parent notice", () => {
  const pages = [
    account({ id: "shared-one", connectionId: "shared-connection", parentNeedsReconnect: true, parentStatus: "invalid" }),
    account({ id: "shared-two", connectionId: "shared-connection", parentNeedsReconnect: true, parentStatus: "invalid" }),
  ];
  const groups = getParentReconnectGroups(pages);

  assert.equal(groups.length, 1);
  assert.deepEqual(groups[0].accounts.map((page) => page.id), ["shared-one", "shared-two"]);
});

test("invalid Page does not affect a valid Page under another connection", () => {
  const pages = [
    account({
      id: "invalid-page",
      connectionId: "invalid-page-connection",
      pageStatus: "invalid",
      pageNeedsReconnect: true,
    }),
    account({ id: "valid-page", connectionId: "valid-page-connection" }),
  ];

  assert.equal(shouldReconnectPage(pages[0]), true);
  assert.equal(shouldReconnectPage(pages[1]), false);
  assert.equal(getParentReconnectGroups(pages).length, 0);
});
