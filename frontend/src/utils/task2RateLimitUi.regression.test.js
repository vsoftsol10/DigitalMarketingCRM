import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import vm from "node:vm";

import formatApiErrorMessage from "./apiErrorMessage.js";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const rateLimitError = {
  response: {
    status: 429,
    data: { success: false, message: "Request was throttled." },
    headers: { "retry-after": "19" },
  },
};

function dataModuleUrl(source) {
  return `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
}

async function sourceUrlWithMocks(filePath, replacements) {
  const source = await readFile(filePath, "utf8");
  const rewritten = source.replace(/(from\s+)(["'])([^"']+)\2/g, (match, prefix, quote, specifier) => {
    const replacement = replacements[specifier] || import.meta.resolve(specifier);
    return `${prefix}${quote}${replacement}${quote}`;
  });
  return dataModuleUrl(rewritten);
}

async function importSourceWithMocks(filePath, replacements, options) {
  return import(await sourceUrlWithMocks(filePath, replacements, options));
}

test("AI caption displays a useful 429 message and makes one generation request", async () => {
  const componentPath = path.join(frontendRoot, "src/components/post/create/ai/AIGenerateButton.jsx");
  const hookPath = path.join(frontendRoot, "src/hooks/mutations/useGenerateAICaption.js");
  const [componentSource, hookSource] = await Promise.all([
    readFile(componentPath, "utf8"),
    readFile(hookPath, "utf8"),
  ]);
  const handleGenerate = componentSource.match(/function handleGenerate\(\) \{[\s\S]*?\n  }/);
  assert.ok(handleGenerate, "AI caption click handler should remain present");
  assert.match(componentSource, /<Alert severity="error"/);
  assert.match(componentSource, /formatApiErrorMessage\(error/);
  assert.doesNotMatch(hookSource, /\bretry\s*:/);

  let apiCalls = 0;
  let capturedPayload;
  let capturedOptions;
  const watch = (field) => ({
    ai_prompt: "synthetic prompt",
    ai_tone: "PROFESSIONAL",
    ai_length: "MEDIUM",
    ai_include_emoji: true,
    ai_include_hashtags: true,
    ai_include_cta: true,
  })[field];
  const mutate = (payload, options) => {
    capturedPayload = payload;
    capturedOptions = options;
    apiCalls += 1;
    return Promise.reject(rateLimitError).catch(() => {});
  };
  const invokeGenerate = vm.runInNewContext(`(${handleGenerate[0]})`, { watch, mutate });
  invokeGenerate();

  assert.equal(apiCalls, 1, "a 429 must not trigger an automatic generation retry");
  assert.equal(capturedPayload.prompt, "synthetic prompt");
  assert.equal(typeof capturedOptions.onSuccess, "function");
  assert.equal(
    formatApiErrorMessage(rateLimitError),
    "Too many requests. Please try again in 19 seconds.",
  );
});

test("media finalization retry reuses the upload session and does not repeat Cloudinary", async () => {
  const file = { name: "synthetic-image.png", type: "image/png" };
  let media = [{ id: "media-1", file, type: "IMAGE", status: "LOCAL" }];
  const uploadResponse = { public_id: "synthetic-upload", version: 7 };
  const state = {
    media,
    effects: [],
    createCalls: 0,
    cloudinaryCalls: 0,
    finalizeCalls: [],
    async createSession() {
      this.createCalls += 1;
      return { session_id: "session-1" };
    },
    async uploadToCloudinary() {
      this.cloudinaryCalls += 1;
      return uploadResponse;
    },
    async finalizeSession(...args) {
      this.finalizeCalls.push(args);
      if (this.finalizeCalls.length === 1) throw rateLimitError;
      return { media_asset_id: "asset-1" };
    },
  };
  globalThis.__rateLimitTestState = state;
  const mockReact = dataModuleUrl(`
    export const useCallback = (fn) => fn;
    export const useEffect = (fn) => { globalThis.__rateLimitTestState.effects.push(fn); };
    export const useRef = (current) => ({ current });
    export const useState = (initial) => [initial, () => {}];
  `);
  const mockReactHookForm = dataModuleUrl(`
    export const useFormContext = () => ({
      watch: () => globalThis.__rateLimitTestState.media,
      setValue: (_name, value) => { globalThis.__rateLimitTestState.media = value; },
      getValues: () => globalThis.__rateLimitTestState.media,
    });
  `);
  const mockMediaUtils = dataModuleUrl(`
    export const createMediaObject = (value) => value;
    export const readImageDimensions = async () => ({ width: 1, height: 1 });
    export const revokePreviewUrl = () => {};
    export const validateMediaFiles = () => ({ accepted: [], rejected: [] });
  `);
  const mockUploadService = dataModuleUrl(`
    export default {
      createSession: (...args) => globalThis.__rateLimitTestState.createSession(...args),
      uploadToCloudinary: (...args) => globalThis.__rateLimitTestState.uploadToCloudinary(...args),
      finalizeSession: (...args) => globalThis.__rateLimitTestState.finalizeSession(...args),
    };
  `);
  const hookFile = path.join(frontendRoot, "src/hooks/post/useMediaUpload.js");
  const { default: useMediaUpload } = await importSourceWithMocks(hookFile, {
    react: mockReact,
    "react-hook-form": mockReactHookForm,
    "../../utils/post/media.utils": mockMediaUtils,
    "../../services/postMediaUpload.service": mockUploadService,
    "../../utils/apiErrorMessage": pathToFileURL(
      path.join(frontendRoot, "src/utils/apiErrorMessage.js"),
    ).href,
  });
  const upload = useMediaUpload({
    config: { accepted_types: ["image/png"], allow_multiple: false },
    organizationId: "org-synthetic",
    uploadPolicy: {},
  });

  state.effects.filter((effect) => typeof effect === "function").forEach((effect) => effect());
  await waitFor(() => state.finalizeCalls.length === 1);
  assert.equal(state.media[0].status, "FAILED");
  assert.match(state.media[0].uploadError, /Too many requests.*19 seconds/);

  upload.retryUpload("media-1");
  await waitFor(() => state.finalizeCalls.length === 2);

  assert.equal(state.createCalls, 1);
  assert.equal(state.cloudinaryCalls, 1);
  assert.equal(state.finalizeCalls[0][0], state.finalizeCalls[1][0]);
  assert.equal(state.finalizeCalls[0][1], state.finalizeCalls[1][1]);
  assert.strictEqual(state.finalizeCalls[0][2], uploadResponse);
  assert.strictEqual(state.finalizeCalls[1][2], uploadResponse);
  assert.equal(state.media[0].status, "UPLOADED");
});

test("Calendar publish and manual retry use the shared formatter for 429 errors", async () => {
  const calendarSource = await readFile(
    path.join(frontendRoot, "src/pages/calendar/Calendar.jsx"),
    "utf8",
  );
  const runAction = calendarSource.match(/async function runAction\([\s\S]*?\n  }/);

  assert.ok(runAction, "Calendar action wrapper should remain present");
  assert.match(runAction[0], /actionInFlightRef\.current/);
  assert.match(runAction[0], /actionType === "publish" \|\| actionType === "retry"/);
  assert.match(runAction[0], /formatApiErrorMessage\(actionError/);
  assert.match(calendarSource, /}, "Unable to retry publishing\.", "retry"\);/);
  const toasts = [];
  let actionCalls = 0;
  const actionContext = {
    actionInFlightRef: { current: false },
    setActionLoading() {},
    setLoadingAction() {},
    formatApiErrorMessage,
    getActionErrorMessage: () => "unexpected fallback",
    toast: { error: (message) => toasts.push(message) },
  };
  const invokeProductionRunAction = vm.runInNewContext(`(${runAction[0]})`, actionContext);
  const rejectedAction = async () => {
    actionCalls += 1;
    throw rateLimitError;
  };

  assert.equal(await invokeProductionRunAction(rejectedAction, "publish fallback", "publish"), false);
  assert.equal(toasts.pop(), "Too many requests. Please try again in 19 seconds.");
  assert.equal(actionCalls, 1);
  assert.equal(await invokeProductionRunAction(rejectedAction, "retry fallback", "retry"), false);
  assert.equal(toasts.pop(), "Too many requests. Please try again in 19 seconds.");
  assert.equal(actionCalls, 2);
  actionContext.actionInFlightRef.current = true;
  assert.equal(await invokeProductionRunAction(rejectedAction, "retry fallback", "retry"), false);
  assert.equal(actionCalls, 2, "the in-flight guard must prevent a duplicate API call");
});

async function waitFor(predicate, timeoutMs = 1000) {
  const deadline = Date.now() + timeoutMs;
  while (!predicate()) {
    if (Date.now() >= deadline) throw new Error("Timed out waiting for mocked upload request.");
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
}
