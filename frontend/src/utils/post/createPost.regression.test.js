import assert from "node:assert/strict";
import test from "node:test";

import { createPostSchema } from "../../validation/createPost.schema.js";
import {
  evaluatePlatform,
  getContentTypeStates,
  getPlatformStates,
  retainSelectedAccountIds,
} from "./platformCapability.utils.js";
import { validateMediaFiles } from "./media.utils.js";
import {
  getUploadChunkSize,
  shouldChunkUpload,
} from "./uploadChunking.js";

const validPng = (name = "valid.png") => ({
  id: name,
  name,
  type: "IMAGE",
  mime_type: "image/png",
  width: 1638,
  height: 2048,
  dimensionsPending: false,
  dimensionsError: null,
});

const tallPng = () => ({
  ...validPng("tall.png"),
  width: 1080,
  height: 1920,
});

test("one 9:16 PNG keeps Instagram Story available but not Post", () => {
  const states = getContentTypeStates({
    platform: "INSTAGRAM",
    media: [tallPng()],
  });

  assert.equal(states.find((state) => state.value === "STORY")?.available, true);
  assert.equal(states.find((state) => state.value === "POST")?.available, false);
});

test("an invalid-ratio image in a multi-image selection disables Instagram", () => {
  const media = [validPng("one.png"), validPng("two.png"), validPng("three.png"), tallPng()];
  assert.equal(evaluatePlatform({ platform: "INSTAGRAM", media }).available, false);
});

test("selected Instagram account is retained and capability returns after invalid media removal", () => {
  const account = { id: "instagram-1", platform: "INSTAGRAM", connected: true, valid: true };
  const invalidMedia = [validPng("valid-one.png"), validPng("valid-two.png"), tallPng()];
  const invalidStates = getPlatformStates({ media: invalidMedia });
  const retained = retainSelectedAccountIds({
    selectedAccountIds: [account.id],
    accounts: [account],
    capabilityMap: new Map(invalidStates.map((state) => [state.platform, state])),
  });

  assert.deepEqual(retained, [account.id]);

  const restoredStates = getPlatformStates({
    media: invalidMedia.filter((item) => item.name !== "tall.png"),
  });
  assert.equal(restoredStates.find((state) => state.platform === "INSTAGRAM")?.available, true);
  assert.deepEqual(
    retainSelectedAccountIds({
      selectedAccountIds: retained,
      accounts: [account],
      capabilityMap: new Map(restoredStates.map((state) => [state.platform, state])),
    }),
    [account.id],
  );
});

test("submit validation rejects selected Instagram with no valid content type", () => {
  const result = createPostSchema.safeParse({
    organization: "org-1",
    platforms: ["INSTAGRAM"],
    social_account_ids: ["instagram-1"],
    platform_content_types: { INSTAGRAM: "POST" },
    media: [validPng("valid-one.png"), validPng("valid-two.png"), tallPng()],
    caption: "A test caption",
    ai_prompt: "",
    ai_tone: "PROFESSIONAL",
    ai_length: "MEDIUM",
    ai_include_emoji: true,
    ai_include_hashtags: true,
    ai_include_cta: true,
    publish_type: "DRAFT",
    timezone: "Asia/Kolkata",
  });

  assert.equal(result.success, false);
  assert.ok(result.error.issues.some((issue) => issue.path[0] === "social_account_ids"));
});

const uploadPolicy = {
  image_max_size_bytes: 10_000_000,
  video_max_size_bytes: 100_000_000,
};

test("shared picker/drop preflight accepts exact byte limits and rejects one byte over", () => {
  const cases = [
    { type: "image/png", limit: 10_000_000, tooLarge: 10_000_001 },
    { type: "video/mp4", limit: 100_000_000, tooLarge: 100_000_001 },
  ];

  for (const source of ["file picker", "drag and drop"]) {
    for (const item of cases) {
      const accepted = validateMediaFiles({
        files: [{ name: `at-limit-${item.type}`, type: item.type, size: item.limit }],
        maxFiles: 10,
        acceptedTypes: [item.type],
        uploadPolicy,
      });
      const rejected = validateMediaFiles({
        files: [{ name: `over-limit-${item.type}`, type: item.type, size: item.tooLarge }],
        maxFiles: 10,
        acceptedTypes: [item.type],
        uploadPolicy,
      });

      assert.equal(accepted.accepted.length, 1, `${source}: exact limit should pass`);
      assert.equal(rejected.rejected[0]?.reason, "FILE_TOO_LARGE", `${source}: over limit should fail`);
    }
  }
});

test("100 MB videos continue to use existing Cloudinary chunk settings", () => {
  const chunkThreshold = 20 * 1024 * 1024;
  const configuredChunkSize = 20 * 1024 * 1024;

  assert.equal(shouldChunkUpload(100_000_000, chunkThreshold), true);
  assert.equal(getUploadChunkSize(configuredChunkSize), configuredChunkSize);
});
