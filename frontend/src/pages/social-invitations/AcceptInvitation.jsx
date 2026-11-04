import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  Container,
  Divider,
  FormControlLabel,
  InputAdornment,
  Portal,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import InstagramIcon from "@mui/icons-material/Instagram";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import socialInvitationService from "../../services/social/socialInvitation.service";

const ACCEPTANCE_KEY = "social_invitation_acceptance";
const RESUMPTION_KEY = "social_invitation_platform_resumption";
const INVITATION_INFO_KEY = "social_invitation_info";
const INVITATION_LINK_TOKEN_KEY = "social_invitation_link_token";
const INVITATION_LINK_PLATFORM_KEY = "social_invitation_link_platform";
const FACEBOOK_SELECTION_KEY = "social_invitation_facebook_selection";
const INSTAGRAM_SELECTION_KEY = "social_invitation_instagram_selection";
const INSTAGRAM_CONFIRMED_KEY = "social_invitation_instagram_confirmed";

const storage = {
  get(key) {
    try {
      return window.sessionStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set(key, value) {
    try {
      window.sessionStorage.setItem(key, value);
      return true;
    } catch {
      // Callers that need cross-navigation persistence must check the result.
      return false;
    }
  },
  remove(key) {
    try {
      window.sessionStorage.removeItem(key);
    } catch {
      // Ignore storage cleanup failures.
    }
  },
};

const hasStoredAcceptanceSession = (acceptanceToken) => {
  if (!acceptanceToken || storage.get(ACCEPTANCE_KEY) !== acceptanceToken) return false;

  const invitationInfo = storage.get(INVITATION_INFO_KEY);
  if (!invitationInfo) return false;

  try {
    const parsedInvitation = JSON.parse(invitationInfo);
    return Boolean(parsedInvitation && typeof parsedInvitation === "object" && !Array.isArray(parsedInvitation));
  } catch {
    return false;
  }
};

const hasStoredResumptionSession = (resumptionToken) => {
  if (!resumptionToken || storage.get(RESUMPTION_KEY) !== resumptionToken) return false;
  const invitationInfo = storage.get(INVITATION_INFO_KEY);
  if (!invitationInfo) return false;
  try {
    const parsed = JSON.parse(invitationInfo);
    return Boolean(parsed && typeof parsed === "object" && !Array.isArray(parsed));
  } catch {
    return false;
  }
};

const persistAcceptanceSession = (acceptanceToken, invitationInfo) => {
  let serializedInvitation;
  try {
    serializedInvitation = JSON.stringify(invitationInfo);
  } catch {
    return false;
  }

  const tokenWriteSucceeded = storage.set(ACCEPTANCE_KEY, acceptanceToken);
  const invitationWriteSucceeded = storage.set(INVITATION_INFO_KEY, serializedInvitation);
  const persisted = Boolean(
    acceptanceToken
    && tokenWriteSucceeded
    && invitationWriteSucceeded
    && storage.get(ACCEPTANCE_KEY) === acceptanceToken
    && storage.get(INVITATION_INFO_KEY) === serializedInvitation
    && hasStoredAcceptanceSession(acceptanceToken),
  );

  if (!persisted) {
    storage.remove(ACCEPTANCE_KEY);
    storage.remove(INVITATION_INFO_KEY);
  }
  return persisted;
};

const persistResumptionSession = (resumptionToken, invitationInfo) => {
  let serializedInvitation;
  try {
    serializedInvitation = JSON.stringify(invitationInfo);
  } catch {
    return false;
  }
  const tokenWritten = storage.set(RESUMPTION_KEY, resumptionToken);
  const infoWritten = storage.set(INVITATION_INFO_KEY, serializedInvitation);
  const persisted = Boolean(
    resumptionToken
    && tokenWritten
    && infoWritten
    && storage.get(RESUMPTION_KEY) === resumptionToken
    && storage.get(INVITATION_INFO_KEY) === serializedInvitation
    && hasStoredResumptionSession(resumptionToken),
  );
  if (!persisted) {
    storage.remove(RESUMPTION_KEY);
    storage.remove(INVITATION_INFO_KEY);
  }
  return persisted;
};

const persistInvitationInfo = (invitationInfo) => {
  try {
    const serializedInvitation = JSON.stringify(invitationInfo);
    return storage.set(INVITATION_INFO_KEY, serializedInvitation)
      && storage.get(INVITATION_INFO_KEY) === serializedInvitation;
  } catch {
    return false;
  }
};

const persistInvitationLinkPlatform = (invitationToken, platform) => {
  if (!invitationToken || !["facebook", "instagram"].includes(platform)) return false;
  try {
    const value = JSON.stringify({ token: invitationToken, platform });
    return storage.set(INVITATION_LINK_PLATFORM_KEY, value)
      && storage.get(INVITATION_LINK_PLATFORM_KEY) === value;
  } catch {
    return false;
  }
};

const getStoredInvitationLinkPlatform = (invitationToken) => {
  if (!invitationToken) return "";
  try {
    const stored = JSON.parse(storage.get(INVITATION_LINK_PLATFORM_KEY) || "null");
    return stored?.token === invitationToken
      && ["facebook", "instagram"].includes(stored?.platform)
      ? stored.platform
      : "";
  } catch {
    return "";
  }
};

const updatePersistedInvitationInfo = (updates) => {
  try {
    const current = JSON.parse(storage.get(INVITATION_INFO_KEY) || "null");
    if (!current || typeof current !== "object" || Array.isArray(current)) return false;
    return persistInvitationInfo({ ...current, ...updates });
  } catch {
    return false;
  }
};

const clearInvitationStorage = () => {
  [
    ACCEPTANCE_KEY,
    RESUMPTION_KEY,
    INVITATION_INFO_KEY,
    INVITATION_LINK_TOKEN_KEY,
    INVITATION_LINK_PLATFORM_KEY,
    FACEBOOK_SELECTION_KEY,
    INSTAGRAM_SELECTION_KEY,
    INSTAGRAM_CONFIRMED_KEY,
  ].forEach(storage.remove);
};

const getErrorMessage = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || error?.message || fallback;

const platformLabel = (platform) => {
  if (platform === "facebook") return "Facebook Pages";
  if (platform === "instagram") return "Instagram account";
  return platform;
};

const fullViewportCenterSx = {
  position: "fixed",
  inset: 0,
  width: "auto",
  height: "auto",
  minHeight: "100vh",
  "@supports (height: 100dvh)": { minHeight: "100dvh" },
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  boxSizing: "border-box",
  m: 0,
};

export default function AcceptInvitation() {
  const invitationLinkTokenRef = useRef("");
  const invitationValidationRef = useRef(null);
  const callbackInfoRef = useRef(null);
  const callbackRequestRef = useRef("");
  const platformResumptionRef = useRef(null);
  const resumptionRequestRef = useRef(null);
  const platformShareClaimRequestRef = useRef(null);
  const instagramAutoConnectRequestsRef = useRef(new Map());
  const facebookAssociationRequestsRef = useRef(new Map());
  const facebookAssociationFailedRef = useRef(new Set());
  const facebookAssociationSessionRef = useRef("");
  const automaticCompletionTokenRef = useRef("");
  const [loading, setLoading] = useState(true);
  const [loadingPlatform, setLoadingPlatform] = useState("");
  const [loadingMessage, setLoadingMessage] = useState("Checking your invitation…");
  const [busy, setBusy] = useState(false);
  const [invitation, setInvitation] = useState(null);
  const [invitationToken, setInvitationToken] = useState("");
  const [acceptanceToken, setAcceptanceToken] = useState("");
  const [credentialType, setCredentialType] = useState("acceptance");
  const [sessionPersistenceReady, setSessionPersistenceReady] = useState(false);
  const [activePlatform, setActivePlatform] = useState("");
  const [platformSpecificFlow, setPlatformSpecificFlow] = useState(false);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [facebookSelectionKey, setFacebookSelectionKey] = useState("");
  const [facebookPages, setFacebookPages] = useState([]);
  const [instagramSelectionKey, setInstagramSelectionKey] = useState("");
  const [instagramPreview, setInstagramPreview] = useState(null);
  const [instagramAccount, setInstagramAccount] = useState(null);
  const [instagramConnectionFailed, setInstagramConnectionFailed] = useState(false);
  const [completionRetryNeeded, setCompletionRetryNeeded] = useState(false);
  const [addedFacebookPageIds, setAddedFacebookPageIds] = useState([]);
  const [connectedPlatforms, setConnectedPlatforms] = useState([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [pageErrors, setPageErrors] = useState({});
  const [addingPageIds, setAddingPageIds] = useState([]);
  const [automaticAssociationPendingIds, setAutomaticAssociationPendingIds] = useState([]);
  const [automaticAssociationFailedIds, setAutomaticAssociationFailedIds] = useState([]);
  const [facebookPageSearch, setFacebookPageSearch] = useState("");
  const [stage, setStage] = useState("loading");
  const [callbackInfo, setCallbackInfo] = useState(null);

  const allowedPlatforms = useMemo(
    () => (Array.isArray(invitation?.platforms) ? invitation.platforms : []),
    [invitation],
  );
  const supportedPlatforms = useMemo(
    () => allowedPlatforms.filter((platform) => ["facebook", "instagram"].includes(platform)),
    [allowedPlatforms],
  );
  const unsupportedPlatforms = useMemo(
    () => allowedPlatforms.filter((platform) => !["facebook", "instagram"].includes(platform)),
    [allowedPlatforms],
  );
  const connectedPlatformSet = new Set([
    ...connectedPlatforms,
    ...(addedFacebookPageIds.length ? ["facebook"] : []),
    ...(instagramAccount ? ["instagram"] : []),
  ]);
  const hasPersistedAccount = connectedPlatformSet.size > 0;
  const facebookComplete = !selectedPlatforms.includes("facebook") || connectedPlatformSet.has("facebook");
  const instagramComplete = !selectedPlatforms.includes("instagram") || connectedPlatformSet.has("instagram");
  const facebookAssociationBlocked = automaticAssociationPendingIds.length > 0 || automaticAssociationFailedIds.length > 0;
  const isComplete = Boolean(acceptanceToken)
    && facebookComplete
    && instagramComplete
    && !facebookAssociationBlocked;
  const isInstagramOnly = selectedPlatforms.length === 1 && selectedPlatforms[0] === "instagram";
  const showFacebookFlow = !platformSpecificFlow || activePlatform === "facebook";
  const showInstagramFlow = !platformSpecificFlow || activePlatform === "instagram";
  const isFacebookPageSelection = stage === "working" && Boolean(facebookSelectionKey);
  const filteredFacebookPages = useMemo(() => {
    const search = facebookPageSearch.trim().toLocaleLowerCase();
    if (!search) return facebookPages;
    return facebookPages.filter((page) =>
      `${page.name || ""} ${page.id || ""}`.toLocaleLowerCase().includes(search),
    );
  }, [facebookPageSearch, facebookPages]);

  const fetchFacebookPages = useCallback(async (token, selectionKey, tokenType = "acceptance") => {
    const result = await socialInvitationService.getFacebookPages(token, selectionKey, tokenType);
    const pages = Array.isArray(result?.pages) ? result.pages : [];
    const associationSessionKey = `${tokenType}:${token}:${selectionKey}`;
    if (facebookAssociationSessionRef.current !== associationSessionKey) {
      facebookAssociationSessionRef.current = associationSessionKey;
      facebookAssociationRequestsRef.current.clear();
      facebookAssociationFailedRef.current.clear();
      setAutomaticAssociationPendingIds([]);
      setAutomaticAssociationFailedIds([]);
    }
    setFacebookPages(pages);
    setFacebookSelectionKey(selectionKey);
    storage.set(FACEBOOK_SELECTION_KEY, selectionKey);
    setStage("working");
  }, []);

  const fetchInstagramPreview = useCallback(async (token, selectionKey, tokenType = "acceptance") => {
    const result = await socialInvitationService.getInstagramPreview(token, selectionKey, tokenType);
    setInstagramPreview(result);
    setInstagramSelectionKey(selectionKey);
    storage.set(INSTAGRAM_SELECTION_KEY, selectionKey);
    setStage("working");
    return result;
  }, []);

  const confirmInstagramConnection = useCallback(async (token, selectionKey, tokenType) => {
    const account = await socialInvitationService.confirmInstagram(
      token,
      selectionKey,
      tokenType,
    );
    setInstagramAccount(account);
    setConnectedPlatforms((current) => current.includes("instagram") ? current : [...current, "instagram"]);
    const storedInfo = (() => {
      try {
        return JSON.parse(storage.get(INVITATION_INFO_KEY) || "null");
      } catch {
        return null;
      }
    })();
    if (storedInfo && typeof storedInfo === "object" && !Array.isArray(storedInfo)) {
      persistInvitationInfo({
        ...storedInfo,
        connectedPlatforms: [...new Set([...(storedInfo.connectedPlatforms || []), "instagram"])],
        platformFinished: storedInfo.platformSpecificFlow && storedInfo.activePlatform === "instagram"
          ? true
          : storedInfo.platformFinished,
      });
    }
    storage.set(INSTAGRAM_CONFIRMED_KEY, JSON.stringify(account));
    storage.remove(INSTAGRAM_SELECTION_KEY);
    setInstagramPreview(null);
    setInstagramSelectionKey("");
    setInstagramConnectionFailed(false);
    setErrorMessage("");
    return account;
  }, []);

  const automaticallyConnectInstagram = useCallback((token, selectionKey, tokenType) => {
    const existingRequest = instagramAutoConnectRequestsRef.current.get(selectionKey);
    if (existingRequest) return existingRequest;

    const request = (async () => {
      try {
        await fetchInstagramPreview(token, selectionKey, tokenType);
        return await confirmInstagramConnection(token, selectionKey, tokenType);
      } catch (error) {
        setInstagramSelectionKey(selectionKey);
        storage.set(INSTAGRAM_SELECTION_KEY, selectionKey);
        setInstagramConnectionFailed(true);
        setErrorMessage(getErrorMessage(error, "Unable to connect this Instagram account. You can retry."));
        throw error;
      }
    })();
    instagramAutoConnectRequestsRef.current.set(selectionKey, request);
    return request;
  }, [confirmInstagramConnection, fetchInstagramPreview]);

  useEffect(() => {
    let active = true;

    const initialize = async () => {
      let redirectingToProvider = false;
      let callbackBlocked = false;
      const currentUrl = new URL(window.location.href);
      const fragmentParams = new URLSearchParams(currentUrl.hash.startsWith("#")
        ? currentUrl.hash.slice(1)
        : "");
      const urlResumptionToken = fragmentParams.get("resume") || "";
      const urlResumptionPlatform = currentUrl.searchParams.get("connect") || "";
      const requestedPlatform = ["facebook", "instagram"].includes(urlResumptionPlatform)
        ? urlResumptionPlatform
        : "";
      if (
        urlResumptionToken
        && requestedPlatform
      ) {
        platformResumptionRef.current = {
          token: urlResumptionToken,
          platform: requestedPlatform,
        };
        setLoadingPlatform(requestedPlatform);
        setLoadingMessage(
          requestedPlatform === "facebook"
            ? "Connecting your Facebook account…"
            : "Connecting your Instagram account…",
        );
      }
      const resumptionToken = platformResumptionRef.current?.token || "";
      const resumptionPlatform = platformResumptionRef.current?.platform || "";
      const urlCallback = {
        facebook: currentUrl.searchParams.get("meta_oauth"),
        facebookSelectionKey: currentUrl.searchParams.get("selection_key"),
        instagram: currentUrl.searchParams.get("instagram_invitation_oauth"),
        instagramSelectionKey: currentUrl.searchParams.get("selection_key"),
      };
      const hasUrlCallback = Boolean(urlCallback.facebook || urlCallback.instagram);
      if (hasUrlCallback) callbackInfoRef.current = urlCallback;

      // The ref preserves callback parameters after the URL is scrubbed and
      // through StrictMode's development-only effect replay.
      const callback = callbackInfoRef.current || urlCallback;
      const hasCallback = Boolean(callback.facebook || callback.instagram);
      const isFacebookCallback = ["selection", "cancelled", "error"].includes(
        callback.facebook,
      );
      const isInstagramCallback = ["preview", "cancelled", "error"].includes(
        callback.instagram,
      );
      const isOAuthCallback = isFacebookCallback || isInstagramCallback;
      if (isOAuthCallback) {
        const callbackPlatform = isFacebookCallback ? "facebook" : "instagram";
        setLoadingPlatform(callbackPlatform);
        setLoadingMessage(
          callbackPlatform === "facebook"
            ? "Connecting your Facebook account…"
            : "Connecting your Instagram account…",
        );
      }
      const isPlatformResumption = Boolean(
        resumptionToken && ["facebook", "instagram"].includes(resumptionPlatform),
      );
      const fragmentToken = !isOAuthCallback && !isPlatformResumption && currentUrl.hash.startsWith("#")
        ? currentUrl.hash.slice(1)
        : "";

      if (fragmentToken) {
        clearInvitationStorage();
        setActivePlatform("");
        setPlatformSpecificFlow(false);
        invitationLinkTokenRef.current = fragmentToken;
        invitationValidationRef.current = null;
        storage.set(INVITATION_LINK_TOKEN_KEY, fragmentToken);
        if (requestedPlatform) {
          persistInvitationLinkPlatform(fragmentToken, requestedPlatform);
        } else {
          storage.remove(INVITATION_LINK_PLATFORM_KEY);
        }
      }

      if (isOAuthCallback) {
        storage.remove(INVITATION_LINK_TOKEN_KEY);
        storage.remove(INVITATION_LINK_PLATFORM_KEY);
        invitationLinkTokenRef.current = "";
        invitationValidationRef.current = null;
      }

      const invitationLinkToken = isOAuthCallback
        ? ""
        : fragmentToken
          || storage.get(INVITATION_LINK_TOKEN_KEY)
          || invitationLinkTokenRef.current
          || "";
      const platformSharePlatform = requestedPlatform && fragmentToken
        ? requestedPlatform
        : getStoredInvitationLinkPlatform(invitationLinkToken);

      if (fragmentToken || currentUrl.search) {
        window.history.replaceState({}, "", currentUrl.pathname);
      }

      if (isPlatformResumption && !isOAuthCallback) {
        clearInvitationStorage();
        invitationLinkTokenRef.current = "";
        invitationValidationRef.current = null;
        const requestRef = resumptionRequestRef.current;
        let resumePromise = requestRef?.token === resumptionToken
          ? requestRef.promise
          : null;
        if (!resumePromise) {
          resumePromise = socialInvitationService.resumePlatform(
            resumptionToken,
            resumptionPlatform,
          );
          resumptionRequestRef.current = { token: resumptionToken, promise: resumePromise };
        }
        try {
          const result = await resumePromise;
          if (!active) return;
          const verifiedPlatform = result.platform;
          const allowedPlatforms = Array.isArray(result.platforms) ? result.platforms : [];
          const responseSelectedPlatforms = Array.isArray(result.selected_platforms)
            ? result.selected_platforms
            : allowedPlatforms;
          if (
            verifiedPlatform !== resumptionPlatform
            || !["facebook", "instagram"].includes(verifiedPlatform)
            || !allowedPlatforms.includes(verifiedPlatform)
            || !responseSelectedPlatforms.includes(verifiedPlatform)
          ) {
            throw new Error("This platform invitation link is invalid or no longer available.");
          }
          const invitationInfo = {
            organization_name: result.organization_name,
            platforms: allowedPlatforms,
            selectedPlatforms: responseSelectedPlatforms,
            connectedPlatforms: result.connected_platforms || [],
            expires_at: result.expires_at,
            activePlatform: verifiedPlatform,
            platformSpecificFlow: true,
            platformFinished: false,
          };
          setAcceptanceToken(resumptionToken);
          setCredentialType("resumption");
          setActivePlatform(verifiedPlatform);
          setPlatformSpecificFlow(true);
          setInvitation(invitationInfo);
          setSelectedPlatforms(invitationInfo.selectedPlatforms);
          setConnectedPlatforms(invitationInfo.connectedPlatforms);
          setSessionPersistenceReady(persistResumptionSession(resumptionToken, invitationInfo));
          setStage("working");
          if (!hasStoredResumptionSession(resumptionToken)) {
            setErrorMessage(
              "Your platform invitation session could not be saved in this browser tab. Enable session storage and reopen the invitation link.",
            );
          } else {
            if (verifiedPlatform === "instagram" && invitationInfo.connectedPlatforms.includes("instagram")) {
              const finishedInfo = { ...invitationInfo, platformFinished: true };
              persistResumptionSession(resumptionToken, finishedInfo);
              setInvitation(finishedInfo);
              setStage("platform-complete");
            } else {
              setBusy(true);
              setErrorMessage("");
              try {
                const started = verifiedPlatform === "facebook"
                  ? await socialInvitationService.startFacebookFromResumption(resumptionToken)
                  : await socialInvitationService.startInstagramFromResumption(resumptionToken);
                const latestInvitationInfo = {
                  ...invitationInfo,
                  connectedPlatforms: started.invitation.connected_platforms || invitationInfo.connectedPlatforms,
                  selectedPlatforms: started.invitation.selected_platforms || invitationInfo.selectedPlatforms,
                  platforms: started.invitation.platforms || invitationInfo.platforms,
                };
                persistResumptionSession(resumptionToken, latestInvitationInfo);
                setInvitation(latestInvitationInfo);
                setConnectedPlatforms(latestInvitationInfo.connectedPlatforms);
                setSelectedPlatforms(latestInvitationInfo.selectedPlatforms);
                redirectingToProvider = true;
                window.location.assign(started.authorization_url);
              } catch (startError) {
                redirectingToProvider = false;
                setErrorMessage(getErrorMessage(startError, `${platformLabel(verifiedPlatform)} authorization is unavailable.`));
              } finally {
                setBusy(false);
              }
            }
          }
        } catch (resumeError) {
          resumptionRequestRef.current = null;
          if (active) {
            setStage("unavailable");
            setErrorMessage(getErrorMessage(resumeError, "This platform invitation link is invalid or no longer available."));
          }
        }
      } else if (invitationLinkToken) {
        try {
          if (!invitationValidationRef.current) {
            invitationValidationRef.current = socialInvitationService.validate(invitationLinkToken);
          }
          const result = await invitationValidationRef.current;
          if (!active) return;
          setInvitation(result);
          setInvitationToken(invitationLinkToken);
          setSelectedPlatforms(Array.isArray(result?.platforms) ? result.platforms : []);
          if (result?.valid && result?.usable) {
            const isPlatformSpecificShareLink = Boolean(
              platformSharePlatform
              && result.platforms?.length === 1
              && result.platforms.includes(platformSharePlatform),
            );
            if (platformSharePlatform && !result.platforms?.includes(platformSharePlatform)) {
              storage.remove(INVITATION_LINK_TOKEN_KEY);
              storage.remove(INVITATION_LINK_PLATFORM_KEY);
              invitationLinkTokenRef.current = "";
              setInvitationToken("");
              setStage("unavailable");
              setErrorMessage("This invitation does not include the requested platform.");
            } else if (isPlatformSpecificShareLink) {
              const platform = platformSharePlatform;
              setBusy(true);
              setLoadingPlatform(platform);
              setLoadingMessage(
                platform === "facebook"
                  ? "Connecting your Facebook account…"
                  : "Connecting your Instagram account…",
              );
              try {
                const requestKey = `${invitationLinkToken}:${platform}`;
                let claimRequest = platformShareClaimRequestRef.current;
                if (!claimRequest || claimRequest.key !== requestKey) {
                  claimRequest = {
                    key: requestKey,
                    promise: socialInvitationService.claim(invitationLinkToken, [platform]),
                  };
                  platformShareClaimRequestRef.current = claimRequest;
                }
                const claimed = await claimRequest.promise;
                if (!active) return;
                const token = claimed?.acceptance_token;
                const acceptedPlatforms = Array.isArray(claimed?.platforms)
                  ? claimed.platforms
                  : [platform];
                if (!token || !acceptedPlatforms.includes(platform)) {
                  throw new Error("The platform invitation session could not be created.");
                }

                const invitationInfo = {
                  ...result,
                  selectedPlatforms: acceptedPlatforms,
                  connectedPlatforms: [],
                  activePlatform: platform,
                  platformSpecificFlow: true,
                  platformFinished: false,
                };
                const sessionPersisted = persistAcceptanceSession(token, invitationInfo);
                storage.remove(INVITATION_LINK_TOKEN_KEY);
                storage.remove(INVITATION_LINK_PLATFORM_KEY);
                invitationLinkTokenRef.current = "";
                invitationValidationRef.current = null;
                setInvitationToken("");
                setAcceptanceToken(token);
                setCredentialType("acceptance");
                setActivePlatform(platform);
                setPlatformSpecificFlow(true);
                setInvitation(invitationInfo);
                setSelectedPlatforms(acceptedPlatforms);
                setConnectedPlatforms([]);
                setSessionPersistenceReady(sessionPersisted);
                setStage("working");

                if (!sessionPersisted) {
                  setErrorMessage(
                    "Your invitation session could not be saved in this browser tab. Retry saving it before authorizing an account.",
                  );
                } else {
                  setErrorMessage("");
                  try {
                    const authorizationUrl = platform === "facebook"
                      ? await socialInvitationService.startFacebook(token)
                      : await socialInvitationService.startInstagram(token);
                    if (!active) return;
                    redirectingToProvider = true;
                    window.location.assign(authorizationUrl);
                  } catch (startError) {
                    if (active) {
                      setErrorMessage(getErrorMessage(
                        startError,
                        `${platformLabel(platform)} authorization is unavailable.`,
                      ));
                    }
                  }
                }
              } catch (claimError) {
                if (platformShareClaimRequestRef.current?.key === `${invitationLinkToken}:${platform}`) {
                  platformShareClaimRequestRef.current = null;
                }
                if (active) {
                  storage.remove(INVITATION_LINK_TOKEN_KEY);
                  storage.remove(INVITATION_LINK_PLATFORM_KEY);
                  invitationLinkTokenRef.current = "";
                  setInvitationToken("");
                  setStage("unavailable");
                  setErrorMessage(getErrorMessage(
                    claimError,
                    "Unable to start this platform invitation.",
                  ));
                }
              } finally {
                if (active) setBusy(false);
              }
            } else {
              setStage("choose");
            }
          } else {
            storage.remove(INVITATION_LINK_TOKEN_KEY);
            storage.remove(INVITATION_LINK_PLATFORM_KEY);
            invitationLinkTokenRef.current = "";
            invitationValidationRef.current = null;
            setStage("unavailable");
            setErrorMessage(
              result?.email_delivery_pending
                ? "This email invitation is not ready yet. Ask the organization owner to resend it when delivery is available."
                : "This invitation is invalid or no longer available. It may have expired, been revoked, or reached its usage limit.",
            );
          }
        } catch (error) {
          if (!active) return;
          if (error?.response?.status >= 400 && error.response.status < 500) {
            storage.remove(INVITATION_LINK_TOKEN_KEY);
            storage.remove(INVITATION_LINK_PLATFORM_KEY);
            invitationLinkTokenRef.current = "";
            invitationValidationRef.current = null;
          }
          setStage("unavailable");
          setErrorMessage(getErrorMessage(error, "Unable to validate this invitation."));
        }
      } else {
        const savedAcceptanceToken = storage.get(ACCEPTANCE_KEY) || "";
        const savedResumptionToken = storage.get(RESUMPTION_KEY) || "";
        const savedInvitation = (() => {
          try {
            return JSON.parse(storage.get(INVITATION_INFO_KEY) || "null");
          } catch {
            return null;
          }
        })();

        const restoredToken = savedResumptionToken || savedAcceptanceToken;
        const restoredCredentialType = savedResumptionToken ? "resumption" : "acceptance";
        const callbackPlatform = isFacebookCallback === isInstagramCallback
          ? ""
          : isFacebookCallback ? "facebook" : "instagram";
        const storedActivePlatform = ["facebook", "instagram"].includes(savedInvitation?.activePlatform)
          ? savedInvitation.activePlatform
          : "";
        const restoredPlatformScoped = savedInvitation?.platformSpecificFlow === true
          || Boolean(savedInvitation && savedResumptionToken && callbackPlatform);
        const restoredActivePlatform = storedActivePlatform
          || (restoredPlatformScoped ? callbackPlatform : "");
        const hasRestoredToken = savedInvitation && (
          restoredCredentialType === "resumption"
            ? hasStoredResumptionSession(savedResumptionToken)
            : hasStoredAcceptanceSession(savedAcceptanceToken)
        );

        if (
          hasCallback
          && (
            (isFacebookCallback && isInstagramCallback)
            || (storedActivePlatform && storedActivePlatform !== callbackPlatform)
            || (restoredPlatformScoped
              && (!callbackPlatform || !restoredActivePlatform || restoredActivePlatform !== callbackPlatform))
          )
        ) {
          callbackBlocked = true;
          setStage("unavailable");
          setErrorMessage("This authorization callback does not match the platform invitation opened in this tab.");
        } else if (restoredToken && hasRestoredToken) {
          let restoredPlatformFinished = savedInvitation.platformFinished === true;
          setSessionPersistenceReady(true);
          setCredentialType(restoredCredentialType);
          setAcceptanceToken(restoredToken);
          setActivePlatform(restoredActivePlatform);
          setPlatformSpecificFlow(restoredPlatformScoped);
          setInvitation({
            ...savedInvitation,
            activePlatform: restoredActivePlatform,
            platformSpecificFlow: restoredPlatformScoped,
          });
          if (savedResumptionToken && callbackPlatform && !storedActivePlatform) {
            persistInvitationInfo({
              ...savedInvitation,
              activePlatform: restoredActivePlatform,
              platformSpecificFlow: restoredPlatformScoped,
            });
          }
          const restoredPlatforms = savedInvitation.selectedPlatforms || savedInvitation.platforms || [];
          setSelectedPlatforms(restoredPlatforms);
          setConnectedPlatforms(savedInvitation.connectedPlatforms || []);
          const restoredFacebookPages = (savedInvitation.connectedPlatforms || []).includes("facebook")
            && Array.isArray(savedInvitation.facebookAddedPages)
            ? savedInvitation.facebookAddedPages
            : [];
          setAddedFacebookPageIds(restoredFacebookPages.map((page) => page.id));
          const savedInstagramAccount = storage.get(INSTAGRAM_CONFIRMED_KEY);
          if (savedInstagramAccount) {
            try {
              setInstagramAccount(JSON.parse(savedInstagramAccount));
            } catch {
              storage.remove(INSTAGRAM_CONFIRMED_KEY);
            }
          }
          const savedFacebookKey = storage.get(FACEBOOK_SELECTION_KEY);
          const savedInstagramKey = storage.get(INSTAGRAM_SELECTION_KEY);
          if (!hasCallback && savedFacebookKey) {
            try {
              await fetchFacebookPages(restoredToken, savedFacebookKey, restoredCredentialType);
            } catch (error) {
              if (active) setErrorMessage(getErrorMessage(error, "Unable to restore Facebook Pages."));
            }
          }
          if (!hasCallback && savedInstagramKey && active) {
            try {
              await automaticallyConnectInstagram(
                restoredToken,
                savedInstagramKey,
                restoredCredentialType,
              );
              if (restoredPlatformScoped && restoredActivePlatform === "instagram") {
                const finishedInfo = {
                  ...savedInvitation,
                  connectedPlatforms: [...new Set([...(savedInvitation.connectedPlatforms || []), "instagram"])],
                  platformFinished: true,
                };
                persistInvitationInfo(finishedInfo);
                setInvitation(finishedInfo);
                restoredPlatformFinished = true;
              }
            } catch (error) {
              if (active) setErrorMessage(getErrorMessage(error, "Unable to restore the Instagram preview."));
            }
          }
          if (active) setStage(restoredPlatformFinished ? "platform-complete" : "working");
        } else if (hasCallback) {
          callbackBlocked = true;
          setStage("unavailable");
          setErrorMessage("This authorization session could not be restored. Reopen the invitation link and try again.");
        } else {
          setStage("unavailable");
          setErrorMessage("This invitation link is missing its token. Open the complete link you received.");
        }
      }

      if (active && hasCallback && !callbackBlocked) {
        setCallbackInfo(callback);
      }
      if (active && callbackBlocked) setLoading(false);
      if (active && !redirectingToProvider && !hasCallback) setLoading(false);
    };

    initialize();
    return () => {
      active = false;
    };
  }, [automaticallyConnectInstagram, fetchFacebookPages, fetchInstagramPreview]);

  useEffect(() => {
    if (!callbackInfo) return;
    const callbackRequestKey = JSON.stringify(callbackInfo);
    if (callbackRequestRef.current === callbackRequestKey) return;
    callbackRequestRef.current = callbackRequestKey;

    if (!acceptanceToken) {
      setErrorMessage("This authorization session could not be restored. Reopen the invitation link and try again.");
      setCallbackInfo(null);
      setLoading(false);
      return;
    }

    const finishCallback = async () => {
      setBusy(true);
      setErrorMessage("");
      try {
        if (callbackInfo.facebook === "selection" && callbackInfo.facebookSelectionKey) {
          await fetchFacebookPages(acceptanceToken, callbackInfo.facebookSelectionKey, credentialType);
        } else if (callbackInfo.facebook === "cancelled") {
          setStatusMessage("Facebook authorization was cancelled. You can try again.");
        } else if (callbackInfo.facebook === "error") {
          setErrorMessage("Facebook authorization could not be completed. You can try again.");
        }

        if (callbackInfo.instagram === "preview" && callbackInfo.instagramSelectionKey) {
          await automaticallyConnectInstagram(
            acceptanceToken,
            callbackInfo.instagramSelectionKey,
            credentialType,
          );
          if (platformSpecificFlow && activePlatform === "instagram") {
            const completedPlatformInfo = {
              ...invitation,
              connectedPlatforms: [...new Set([...(invitation.connectedPlatforms || []), "instagram"])],
              platformFinished: true,
            };
            persistInvitationInfo(completedPlatformInfo);
            setInvitation(completedPlatformInfo);
            setStage("platform-complete");
          }
        } else if (callbackInfo.instagram === "cancelled") {
          setStatusMessage("Instagram authorization was cancelled. You can try again.");
        } else if (callbackInfo.instagram === "error") {
          setErrorMessage("Instagram authorization could not be completed. You can try again.");
        }
      } catch (error) {
        setErrorMessage(getErrorMessage(error, "Unable to continue this authorization."));
      } finally {
        setBusy(false);
        setCallbackInfo(null);
        setLoading(false);
      }
    };

    finishCallback();
  }, [acceptanceToken, activePlatform, automaticallyConnectInstagram, callbackInfo, credentialType, fetchFacebookPages, invitation, platformSpecificFlow]);

  const togglePlatform = (platform) => {
    setSelectedPlatforms((current) => current.includes(platform)
      ? current.filter((item) => item !== platform)
      : [...current, platform]);
  };

  const handleClaim = async () => {
    if (!invitationToken || selectedPlatforms.length === 0 || busy) return;
    setBusy(true);
    setErrorMessage("");
    try {
      const result = await socialInvitationService.claim(invitationToken, selectedPlatforms);
      const token = result?.acceptance_token;
      if (!token) throw new Error("The invitation session token was not returned.");
      const acceptedPlatforms = Array.isArray(result.platforms) ? result.platforms : selectedPlatforms;
      const invitationInfo = {
        ...invitation,
        selectedPlatforms: acceptedPlatforms,
        activePlatform: "",
        platformSpecificFlow: false,
        platformFinished: false,
      };
      const sessionPersisted = persistAcceptanceSession(token, invitationInfo);
      storage.remove(INVITATION_LINK_TOKEN_KEY);
      storage.remove(INVITATION_LINK_PLATFORM_KEY);
      invitationLinkTokenRef.current = "";
      invitationValidationRef.current = null;
      setSessionPersistenceReady(sessionPersisted);
      setCredentialType("acceptance");
      setActivePlatform("");
      setPlatformSpecificFlow(false);
      setConnectedPlatforms([]);
      setAcceptanceToken(token);
      setInvitation(invitationInfo);
      setInvitationToken("");
      setSelectedPlatforms(acceptedPlatforms);
      setStage("working");
      if (sessionPersisted) {
        setErrorMessage("");
        setStatusMessage("Invitation accepted. Choose a platform to authorize.");
      } else {
        setStatusMessage("");
        setErrorMessage(
          "Your invitation session could not be saved in this browser tab. Retry saving it before authorizing an account.",
        );
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "Unable to start this invitation."));
    } finally {
      setBusy(false);
    }
  };

  const retryAcceptanceSessionPersistence = () => {
    if (!acceptanceToken || !invitation || busy) return;
    const persisted = credentialType === "resumption"
      ? persistResumptionSession(acceptanceToken, invitation)
      : persistAcceptanceSession(acceptanceToken, invitation);
    setSessionPersistenceReady(persisted);
    if (persisted) {
      setErrorMessage("");
      setStatusMessage("Invitation session saved. You can authorize your selected accounts now.");
    } else {
      setErrorMessage(
        "Your invitation session could not be saved in this browser tab. Enable session storage and retry.",
      );
    }
  };

  const startOAuth = async (platform) => {
    if (!acceptanceToken || busy) return;
    if (platformSpecificFlow && platform !== activePlatform) {
      setErrorMessage("This link only authorizes the platform selected in the invitation email.");
      return;
    }
    const storedSessionIsValid = credentialType === "resumption"
      ? hasStoredResumptionSession(acceptanceToken)
      : hasStoredAcceptanceSession(acceptanceToken);
    if (!sessionPersistenceReady || !storedSessionIsValid) {
      setSessionPersistenceReady(false);
      setErrorMessage(
        "Your invitation session is not available in this browser tab. Retry saving it before authorizing an account.",
      );
      return;
    }
    setBusy(true);
    setErrorMessage("");
    try {
      const oauthInvitationInfo = {
        ...invitation,
        activePlatform: platform,
        platformSpecificFlow,
        platformFinished: false,
      };
      if (!persistInvitationInfo(oauthInvitationInfo)) {
        throw new Error("Your invitation platform could not be saved in this browser tab. Retry before authorizing.");
      }
      setActivePlatform(platform);
      setInvitation(oauthInvitationInfo);
      if (credentialType === "resumption") {
        const started = platform === "facebook"
          ? await socialInvitationService.startFacebookFromResumption(acceptanceToken)
          : await socialInvitationService.startInstagramFromResumption(acceptanceToken);
        const updatedInvitation = {
          ...oauthInvitationInfo,
          connectedPlatforms: started.invitation.connected_platforms || oauthInvitationInfo.connectedPlatforms || [],
          selectedPlatforms: started.invitation.selected_platforms || oauthInvitationInfo.selectedPlatforms || [],
        };
        persistInvitationInfo(updatedInvitation);
        setInvitation(updatedInvitation);
        setConnectedPlatforms(updatedInvitation.connectedPlatforms);
        window.location.assign(started.authorization_url);
      } else {
        const authorizationUrl = platform === "facebook"
          ? await socialInvitationService.startFacebook(acceptanceToken)
          : await socialInvitationService.startInstagram(acceptanceToken);
        window.location.assign(authorizationUrl);
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, `${platformLabel(platform)} authorization is unavailable.`));
      setBusy(false);
    }
  };

  const markPlatformFinished = () => {
    setStage("platform-complete");
    setInvitation((current) => current ? { ...current, platformFinished: true } : current);
    updatePersistedInvitationInfo({ platformFinished: true });
  };

  const handleAddFacebookPage = useCallback(async (page) => {
    if (!acceptanceToken || !facebookSelectionKey || addingPageIds.includes(page.id)) return false;
    setAddingPageIds((current) => [...current, page.id]);
    setPageErrors((current) => ({ ...current, [page.id]: "" }));
    try {
      await socialInvitationService.addFacebookPage(
        acceptanceToken,
        facebookSelectionKey,
        page.id,
        credentialType,
      );
      setFacebookPages((current) => current.map((item) =>
        item.id === page.id ? { ...item, connected: true } : item));
      setAddedFacebookPageIds((current) => current.includes(page.id) ? current : [...current, page.id]);
      setConnectedPlatforms((current) => current.includes("facebook") ? current : [...current, "facebook"]);
      const addedPageSummary = { id: page.id, name: page.name };
      const currentStoredInfo = (() => {
        try {
          return JSON.parse(storage.get(INVITATION_INFO_KEY) || "null");
        } catch {
          return null;
        }
      })();
      const storedPages = Array.isArray(currentStoredInfo?.facebookAddedPages)
        ? currentStoredInfo.facebookAddedPages
        : [];
      updatePersistedInvitationInfo({
        connectedPlatforms: [...new Set([...(currentStoredInfo?.connectedPlatforms || []), "facebook"])],
        facebookAddedPages: [
          ...storedPages.filter((item) => item.id !== page.id),
          addedPageSummary,
        ],
      });
      setStatusMessage(`${page.name} is connected. You can add another Page.`);
      return true;
    } catch (error) {
      setPageErrors((current) => ({
        ...current,
        [page.id]: getErrorMessage(error, `Unable to connect ${page.name}.`),
      }));
      return false;
    } finally {
      setAddingPageIds((current) => current.filter((id) => id !== page.id));
    }
  }, [acceptanceToken, addingPageIds, credentialType, facebookSelectionKey]);

  const automaticallyAssociateFacebookPage = useCallback((page) => {
    const pageId = String(page?.id || "");
    if (!acceptanceToken || !facebookSelectionKey || !pageId || !page?.connected) return;
    if (addedFacebookPageIds.includes(pageId)) return;

    const requestKey = `${credentialType}:${acceptanceToken}:${facebookSelectionKey}:${pageId}`;
    if (
      facebookAssociationRequestsRef.current.has(requestKey)
      || facebookAssociationFailedRef.current.has(requestKey)
    ) {
      return;
    }

    setAutomaticAssociationPendingIds((current) => current.includes(pageId) ? current : [...current, pageId]);
    const request = (async () => {
      const succeeded = await handleAddFacebookPage(page);
      if (succeeded) {
        setAutomaticAssociationFailedIds((current) => current.filter((id) => id !== pageId));
      } else {
        facebookAssociationFailedRef.current.add(requestKey);
        setAutomaticAssociationFailedIds((current) => current.includes(pageId) ? current : [...current, pageId]);
      }
      setAutomaticAssociationPendingIds((current) => current.filter((id) => id !== pageId));
    })();
    facebookAssociationRequestsRef.current.set(requestKey, request);
  }, [acceptanceToken, addedFacebookPageIds, credentialType, facebookSelectionKey, handleAddFacebookPage]);

  const retryFacebookPageAssociation = (page) => {
    const pageId = String(page?.id || "");
    if (!pageId) return;
    const requestKey = `${credentialType}:${acceptanceToken}:${facebookSelectionKey}:${pageId}`;
    facebookAssociationRequestsRef.current.delete(requestKey);
    facebookAssociationFailedRef.current.delete(requestKey);
    setAutomaticAssociationFailedIds((current) => current.filter((id) => id !== pageId));
  };

  useEffect(() => {
    if (!acceptanceToken || !facebookSelectionKey || !facebookPages.length) return;
    facebookPages
      .filter((page) => page?.connected && !addedFacebookPageIds.includes(String(page.id || "")))
      .forEach(automaticallyAssociateFacebookPage);
  }, [
    acceptanceToken,
    addedFacebookPageIds,
    automaticAssociationFailedIds,
    credentialType,
    facebookPages,
    facebookSelectionKey,
    automaticallyAssociateFacebookPage,
  ]);

  const handleConfirmInstagram = async () => {
    if (!acceptanceToken || !instagramSelectionKey || busy) return;
    setBusy(true);
    setErrorMessage("");
    setInstagramConnectionFailed(false);
    try {
      await confirmInstagramConnection(
        acceptanceToken,
        instagramSelectionKey,
        credentialType,
      );
      if (platformSpecificFlow && activePlatform === "instagram") {
        markPlatformFinished();
      }
    } catch (error) {
      setInstagramConnectionFailed(true);
      setErrorMessage(getErrorMessage(error, "Unable to connect this Instagram account."));
    } finally {
      setBusy(false);
    }
  };

  const handleDeclineInstagram = async () => {
    if (!acceptanceToken || !instagramSelectionKey || busy) return;
    setBusy(true);
    setErrorMessage("");
    try {
      await socialInvitationService.declineInstagram(
        acceptanceToken,
        instagramSelectionKey,
        credentialType,
      );
      setInstagramPreview(null);
      storage.remove(INSTAGRAM_SELECTION_KEY);
      setInstagramSelectionKey("");
      setInstagramConnectionFailed(false);
      setStatusMessage("Instagram authorization was discarded. You can authorize it again at any time.");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "Unable to decline this Instagram authorization."));
    } finally {
      setBusy(false);
    }
  };

  const handleCancel = async () => {
    if (!acceptanceToken || busy || hasPersistedAccount || credentialType === "resumption") return;
    setBusy(true);
    setErrorMessage("");
    try {
      await socialInvitationService.cancel(acceptanceToken);
      clearInvitationStorage();
      setAcceptanceToken("");
      setStage("cancelled");
      setStatusMessage("This invitation session was cancelled.");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "Unable to cancel this invitation session."));
    } finally {
      setBusy(false);
    }
  };

  const handleFinish = useCallback(async () => {
    if (!isComplete || busy || !acceptanceToken) return;
    setBusy(true);
    setErrorMessage("");
    setStatusMessage("");
    setCompletionRetryNeeded(false);
    try {
      const result = await socialInvitationService.complete(acceptanceToken, credentialType);
      if (result?.status !== "completed") {
        throw new Error("The invitation completion was not confirmed.");
      }
      clearInvitationStorage();
      setAcceptanceToken("");
      setStage("complete");
      setCompletionRetryNeeded(false);
    } catch (error) {
      if (error?.response?.data?.code === "incomplete_accounts") {
        setStatusMessage(error.response.data.message || "Connect the remaining selected accounts to finish.");
      } else {
        setErrorMessage(getErrorMessage(error, "Unable to complete this invitation."));
      }
      setCompletionRetryNeeded(true);
    } finally {
      setBusy(false);
    }
  }, [acceptanceToken, busy, credentialType, isComplete]);

  const handleFinishFacebookPlatform = async () => {
    if (!platformSpecificFlow || activePlatform !== "facebook" || busy) return;
    if (!connectedPlatformSet.has("facebook")) return;
    if (isComplete) {
      await handleFinish();
      return;
    }
    markPlatformFinished();
  };

  useEffect(() => {
    if (
      loading
      || !["working", "platform-complete"].includes(stage)
      || !(isInstagramOnly || (platformSpecificFlow && activePlatform === "instagram"))
      || !isComplete
      || busy
      || !acceptanceToken
      || automaticCompletionTokenRef.current === acceptanceToken
    ) {
      return;
    }
    automaticCompletionTokenRef.current = acceptanceToken;
    handleFinish();
  }, [acceptanceToken, activePlatform, busy, handleFinish, isComplete, isInstagramOnly, loading, platformSpecificFlow, stage]);

  if (!loading && stage === "platform-complete" && platformSpecificFlow) {
    return (
      <Portal>
        <Box component="main" sx={{ ...fullViewportCenterSx, zIndex: 1300, px: 2, py: 2 }}>
          <Stack alignItems="center" spacing={1} sx={{ width: "100%", maxWidth: 560, mx: "auto" }}>
            <CheckCircleOutlineRoundedIcon sx={{ fontSize: 28, color: "success.main" }} aria-hidden="true" />
            <Typography component="h1" variant="h5" fontWeight={700} textAlign="center" sx={{ lineHeight: 1.25 }}>
              {activePlatform === "facebook" ? "Facebook connected successfully" : "Instagram connected successfully"}
            </Typography>
            <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ lineHeight: 1.55 }}>
              {activePlatform === "facebook"
                ? `Your Facebook Pages are connected to ${invitation?.organization_name || "the organization"}.`
                : `Your Instagram account is connected to ${invitation?.organization_name || "the organization"}.`}
            </Typography>
            {errorMessage && <Alert severity="error" sx={{ width: "100%" }}>{errorMessage}</Alert>}
            {isComplete && completionRetryNeeded && (
              <Button variant="contained" onClick={handleFinish} disabled={busy}>
                {busy ? <CircularProgress size={20} color="inherit" /> : "Retry invitation completion"}
              </Button>
            )}
          </Stack>
        </Box>
      </Portal>
    );
  }

  if (loading) {
    const loadingLabel = loadingPlatform === "facebook"
      ? "Connecting your Facebook account…"
      : loadingPlatform === "instagram"
        ? "Connecting your Instagram account…"
        : loadingMessage;

    return (
      <Portal>
        <Box component="main" sx={{ ...fullViewportCenterSx, zIndex: 1300, px: 2, bgcolor: "#f8fafc" }}>
          <Stack
            role="status"
            aria-live="polite"
            direction="column"
            alignItems="center"
            justifyContent="center"
            spacing={1.5}
            textAlign="center"
            sx={{ width: "100%", maxWidth: 400, mx: "auto" }}
          >
            <CircularProgress size={28} thickness={4} aria-label="Loading" />
            <Typography variant="body2" fontWeight={600} color="text.primary" textAlign="center">
              {loadingLabel}
            </Typography>
          </Stack>
        </Box>
      </Portal>
    );
  }

  if (stage === "complete") {
    return (
      <Portal>
        <Box component="main" sx={{ ...fullViewportCenterSx, px: 2, py: 2 }}>
          <Stack alignItems="center" spacing={1} sx={{ width: "100%", maxWidth: 560, mx: "auto" }}>
            <CheckCircleOutlineRoundedIcon sx={{ fontSize: 28, color: "success.main" }} aria-hidden="true" />
            <Typography component="h1" variant="h5" fontWeight={700} textAlign="center" sx={{ lineHeight: 1.25 }}>
              {platformSpecificFlow && activePlatform === "facebook"
                ? "Facebook connected successfully"
                : platformSpecificFlow && activePlatform === "instagram"
                  ? "Instagram connected successfully"
                  : "Social accounts connected successfully"}
            </Typography>
            <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ lineHeight: 1.55 }}>
              {platformSpecificFlow && activePlatform === "facebook"
                ? `Your Facebook Pages are connected to ${invitation?.organization_name || "the organization"}.`
                : platformSpecificFlow && activePlatform === "instagram"
                  ? `Your Instagram account is connected to ${invitation?.organization_name || "the organization"}.`
                  : `Your social accounts are connected to ${invitation?.organization_name || "the organization"}.`}
            </Typography>
          </Stack>
        </Box>
      </Portal>
    );
  }

  if (isFacebookPageSelection) {
    return (
      <Box
        component="main"
        sx={{
          width: "100%",
          minHeight: "100vh",
          "@supports (min-height: 100dvh)": { minHeight: "100dvh" },
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxSizing: "border-box",
          bgcolor: "#f5f7fb",
          px: { xs: 1.5, sm: 2 },
          py: { xs: 2, sm: 3 },
        }}
      >
        <Card
          square
          elevation={0}
          sx={{
            width: "100%",
            maxWidth: 760,
            border: "1px solid #d9e0e8",
            borderRadius: 0,
            boxSizing: "border-box",
            bgcolor: "#fff",
          boxShadow: "0 10px 30px rgba(25, 42, 70, 0.08)",
          }}
        >
          <CardContent sx={{ p: { xs: 2, sm: 3.25 }, "&:last-child": { pb: { xs: 2, sm: 3.25 } } }}>
            <Stack spacing={{ xs: 1.75, sm: 2.25 }}>
              <Typography component="h1" variant="h6" fontWeight={700} textAlign="left" sx={{ color: "#172b4d", letterSpacing: "-0.01em" }}>
                Select the Facebook Pages you want to connect to your organization.
              </Typography>

              <TextField
                fullWidth
                size="small"
                placeholder="Search Facebook Pages"
                value={facebookPageSearch}
                onChange={(event) => setFacebookPageSearch(event.target.value)}
                inputProps={{ "aria-label": "Search Facebook Pages" }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchRoundedIcon color="action" />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  "& .MuiOutlinedInput-root": { borderRadius: 0, bgcolor: "#fff" },
                }}
              />

              <Stack spacing={1.25}>
                {!facebookPages.length ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                    No eligible Facebook Pages were found.
                  </Typography>
                ) : filteredFacebookPages.length ? filteredFacebookPages.map((page) => {
                  const isAdded = addedFacebookPageIds.includes(page.id);
                  const isConnected = Boolean(page.connected);
                  const isAdding = addingPageIds.includes(page.id);
                  const isAssociationPending = automaticAssociationPendingIds.includes(page.id);
                  const isAssociationFailed = automaticAssociationFailedIds.includes(page.id);

                  return (
                    <Card
                      key={page.id}
                      square
                      variant="outlined"
                      sx={{
                        borderRadius: 0,
                        bgcolor: "#fff",
                        borderColor: "#d8e0ea",
                        transition: "border-color 140ms ease, box-shadow 140ms ease",
                        "&:hover": {
                          borderColor: "#b6c4d5",
                          boxShadow: "0 2px 8px rgba(25, 42, 70, 0.06)",
                        },
                      }}
                    >
                      <CardContent sx={{ p: { xs: 1.25, sm: 1.5 }, "&:last-child": { pb: { xs: 1.25, sm: 1.5 } } }}>
                        <Stack
                          direction={{ xs: "column", sm: "row" }}
                          spacing={1.25}
                          alignItems={{ xs: "stretch", sm: "center" }}
                        >
                          <Stack direction="row" spacing={1.25} alignItems="center" sx={{ flex: 1, minWidth: 0 }}>
                            <Avatar sx={{ width: 34, height: 34, flexShrink: 0, bgcolor: "#eaf2ff", color: "#1877f2" }}>
                              <FacebookRoundedIcon fontSize="small" />
                            </Avatar>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography variant="subtitle1" fontWeight={700} sx={{ color: "#172b4d", lineHeight: 1.3, overflowWrap: "anywhere" }}>
                                {page.name}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" display="block" sx={{ mt: 0.35 }}>
                                Facebook Page
                              </Typography>
                              {page.id && (
                                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.15, overflowWrap: "anywhere" }}>
                                  Page ID: {page.id}
                                </Typography>
                              )}
                            </Box>
                          </Stack>
                          <Stack direction="row" spacing={1} alignItems="center" justifyContent="flex-end" sx={{ width: { xs: "100%", sm: "auto" } }}>
                            {isAdded ? (
                              <Stack direction="row" spacing={0.5} alignItems="center" sx={{ color: "success.main" }}>
                                <CheckCircleOutlineRoundedIcon fontSize="small" aria-hidden="true" />
                                <Typography variant="body2" fontWeight={600} color="success.main">
                                  Connected
                                </Typography>
                              </Stack>
                            ) : isConnected ? (
                              <Stack direction="row" spacing={0.5} alignItems="center" sx={{ color: "success.main" }}>
                                {isAssociationPending ? <CircularProgress size={16} color="inherit" /> : <CheckCircleOutlineRoundedIcon fontSize="small" aria-hidden="true" />}
                                <Typography variant="body2" fontWeight={600} color="success.main">
                                  {isAssociationPending ? "Associating..." : "Connected"}
                                </Typography>
                              </Stack>
                            ) : (
                              <Button
                                size="small"
                                variant="contained"
                                color="primary"
                                disabled={isAdding}
                                onClick={() => handleAddFacebookPage(page)}
                                aria-label={`Add Page ${page.name} to this invitation`}
                                startIcon={isAdding ? <CircularProgress size={15} /> : null}
                                sx={{
                                  minWidth: { xs: "100%", sm: 92 },
                                  minHeight: 34,
                                  borderRadius: 0,
                                  whiteSpace: "nowrap",
                                }}
                              >
                                {isAdding ? "Adding" : "Add"}
                              </Button>
                            )}
                          </Stack>
                        </Stack>
                        {pageErrors[page.id] && (
                          <Alert
                            severity="error"
                            action={isAssociationFailed ? <Button color="inherit" size="small" onClick={() => retryFacebookPageAssociation(page)}>Retry association</Button> : undefined}
                            sx={{ mt: 1.25, borderRadius: 0 }}
                          >
                            {pageErrors[page.id]}
                          </Alert>
                        )}
                      </CardContent>
                    </Card>
                  );
                }) : (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                    No Pages match your search.
                  </Typography>
                )}
              </Stack>

              {errorMessage && <Alert severity="error" sx={{ borderRadius: 0 }}>{errorMessage}</Alert>}

              {platformSpecificFlow && activePlatform === "facebook" && addedFacebookPageIds.length > 0 && (
                <Button
                  variant="contained"
                  onClick={handleFinishFacebookPlatform}
                  disabled={busy || facebookAssociationBlocked}
                  sx={{ alignSelf: { xs: "stretch", sm: "flex-end" }, minHeight: 40, borderRadius: 0 }}
                >
                  {busy
                    ? <CircularProgress size={20} color="inherit" />
                    : "I’m Done Adding"}
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
      <Box
        sx={{
          width: "100%",
          minHeight: "100dvh",
          bgcolor: "#f5f7fb",
          py: isFacebookPageSelection ? { xs: 2, sm: 4 } : { xs: 3, md: 7 },
          ...(isFacebookPageSelection && {
            display: "flex",
            justifyContent: "center",
          }),
        }}
      >
      <Container
        maxWidth={false}
        sx={{
          maxWidth: isFacebookPageSelection ? 820 : 600,
          width: "100%",
          mx: "auto",
          px: { xs: 1.5, sm: 2 },
        }}
      >
        <Card
          elevation={0}
          sx={{
            border: "1px solid #e4e9f1",
            borderRadius: 3,
            boxShadow: isFacebookPageSelection ? "0 8px 24px rgba(16, 24, 40, 0.06)" : "none",
          }}
        >
          <CardContent sx={{ p: isFacebookPageSelection ? { xs: 2, sm: 2.75 } : { xs: 3, md: 5 } }}>
            <Stack spacing={isFacebookPageSelection ? 2 : 3}>
              <Box>
                <Typography variant="overline" color="primary.main" fontWeight={700}>
                  SOCIAL ACCOUNT INVITATION
                </Typography>
                <Typography variant="h4" fontWeight={700} sx={{ mt: 0.5, fontSize: { xs: 26, md: 32 } }}>
                  {platformSpecificFlow && activePlatform
                    ? `Connect your ${activePlatform === "facebook" ? "Facebook Pages" : "Instagram account"}`
                    : "Connect your social accounts"}
                </Typography>
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  {platformSpecificFlow && activePlatform
                    ? `Connect ${activePlatform === "facebook" ? "one or more Facebook Pages" : "your Instagram Business account"} to ${invitation?.organization_name || "the organization"}.`
                    : invitation?.organization_name
                      ? `${invitation.organization_name} invited you to connect social accounts.`
                      : "Review the invitation and authorize the accounts you want to connect."}
                </Typography>
              </Box>

              {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
              {statusMessage && <Alert severity="info">{statusMessage}</Alert>}
              {stage === "working" && acceptanceToken && !sessionPersistenceReady && (
                <Button
                  variant="outlined"
                  onClick={retryAcceptanceSessionPersistence}
                  disabled={busy}
                >
                  Retry saving invitation session
                </Button>
              )}

              {stage === "choose" && invitation?.usable && (
                <>
                  <Box>
                    <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                      Platforms included
                    </Typography>
                    <Stack spacing={0.5}>
                      {supportedPlatforms.map((platform) => (
                        <FormControlLabel
                          key={platform}
                          control={(
                            <Checkbox
                              checked={selectedPlatforms.includes(platform)}
                              onChange={() => togglePlatform(platform)}
                            />
                          )}
                          label={platformLabel(platform)}
                        />
                      ))}
                      {unsupportedPlatforms.map((platform) => (
                        <FormControlLabel
                          key={platform}
                          disabled
                          control={<Checkbox checked={false} />}
                          label={`${platformLabel(platform)} (not available yet)`}
                        />
                      ))}
                    </Stack>
                    {!supportedPlatforms.length && (
                      <Alert severity="warning" sx={{ mt: 1 }}>
                        This invitation does not include a supported platform.
                      </Alert>
                    )}
                  </Box>
                  <Button
                    variant="contained"
                    size="large"
                    disabled={busy || !selectedPlatforms.some((platform) => supportedPlatforms.includes(platform))}
                    onClick={handleClaim}
                  >
                    {busy ? <CircularProgress size={22} color="inherit" /> : "Continue"}
                  </Button>
                </>
              )}

              {stage === "working" && (
                <Stack spacing={2.5}>
                  {selectedPlatforms.includes("facebook") && showFacebookFlow && (
                    <Box sx={{ border: isFacebookPageSelection ? "none" : "1px solid #dbe6f5", borderRadius: 3, bgcolor: isFacebookPageSelection ? "transparent" : "#f8fbff", p: isFacebookPageSelection ? 0 : { xs: 1.5, sm: 2 } }}>
                      {!facebookSelectionKey && (
                      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} alignItems={{ xs: "stretch", sm: "center" }} justifyContent="space-between">
                        <Stack direction="row" spacing={1.25} alignItems="center">
                          <Avatar sx={{ bgcolor: "#e9f0ff", color: "#1877f2", width: 46, height: 46 }}>
                            <FacebookRoundedIcon />
                          </Avatar>
                          <Box>
                            <Typography variant="h6" fontWeight={700}>Facebook Pages</Typography>
                            <Typography variant="body2" color="text.secondary">Choose one or more Pages to connect</Typography>
                          </Box>
                        </Stack>
                        {!facebookSelectionKey && (
                          <Button
                            variant="contained"
                            disabled={busy || !sessionPersistenceReady}
                            onClick={() => startOAuth("facebook")}
                            sx={{ borderRadius: 2, minWidth: { xs: "100%", sm: 124 } }}
                          >
                            Authorize
                          </Button>
                        )}
                      </Stack>
                      )}
                      {facebookSelectionKey && (
                        <Stack spacing={1} sx={{ mt: 1.5 }}>
                          <TextField
                            fullWidth
                            size="small"
                            placeholder="Search Facebook Pages"
                            value={facebookPageSearch}
                            onChange={(event) => setFacebookPageSearch(event.target.value)}
                            inputProps={{ "aria-label": "Search Facebook Pages" }}
                            InputProps={{
                              startAdornment: (
                                <InputAdornment position="start">
                                  <SearchRoundedIcon color="action" />
                                </InputAdornment>
                              ),
                            }}
                            sx={{
                              mb: 0.25,
                              "& .MuiOutlinedInput-root": { borderRadius: 2, bgcolor: "#fff" },
                            }}
                          />
                          <Box sx={{ px: 0.25, py: 0.25 }}>
                            <Typography variant="body2" fontWeight={600}>
                              Select the Facebook Pages you want to connect to your organization.
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              All Pages available to your Facebook account are listed below. Select only the Pages you want to connect.
                            </Typography>
                          </Box>
                          {!facebookPages.length ? (
                            <Box sx={{ textAlign: "center", py: 2, px: 1.5, bgcolor: "#fff", border: "1px dashed #cbd5e1", borderRadius: 2 }}>
                              <Typography fontWeight={700}>No eligible Pages found</Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                Make sure your Facebook account has access to a Page and try authorizing again.
                              </Typography>
                            </Box>
                          ) : filteredFacebookPages.length ? filteredFacebookPages.map((page) => {
                            const isAdded = addedFacebookPageIds.includes(page.id);
                            const isConnected = Boolean(page.connected);
                            const isAdding = addingPageIds.includes(page.id);
                            const isAssociationPending = automaticAssociationPendingIds.includes(page.id);
                            const isAssociationFailed = automaticAssociationFailedIds.includes(page.id);

                            return (
                            <Card
                              key={page.id}
                              variant="outlined"
                              sx={{
                                borderRadius: 0,
                                bgcolor: "#fff",
                                transition: "border-color 160ms ease, box-shadow 160ms ease",
                                "&:hover": { borderColor: "#98a2b3", boxShadow: "0 4px 14px rgba(16, 24, 40, 0.06)" },
                              }}
                            >
                              <CardContent sx={{ p: { xs: 1.25, sm: 1.5 }, "&:last-child": { pb: { xs: 1.25, sm: 1.5 } } }}>
                                <Stack direction={{ xs: "column", sm: "row" }} spacing={1.25} alignItems={{ xs: "stretch", sm: "center" }}>
                                  <Stack direction="row" spacing={1.25} alignItems="center" sx={{ flex: 1, minWidth: 0 }}>
                                    <Avatar src={page.profile_image || undefined} alt="" sx={{ width: 36, height: 36, flexShrink: 0, bgcolor: "#e9f0ff", color: "#1877f2" }}>
                                      <FacebookRoundedIcon />
                                    </Avatar>
                                    <Box sx={{ flex: 1, minWidth: 0 }}>
                                      <Typography variant="body2" fontWeight={700} noWrap>{page.name}</Typography>
                                      <Typography variant="caption" color="text.secondary" display="block">Facebook Page</Typography>
                                      <Typography variant="caption" color="text.secondary" sx={{ display: "block", overflowWrap: "anywhere" }}>
                                        Page ID: {page.id}
                                      </Typography>
                                    </Box>
                                  </Stack>
                                  <Stack
                                    direction="row"
                                    spacing={0.75}
                                    alignItems="center"
                                    justifyContent="flex-end"
                                    sx={{ width: { xs: "100%", sm: "auto" } }}
                                  >
                                    {isAdded ? (
                                      <Stack direction="row" spacing={0.5} alignItems="center" sx={{ color: "success.main" }}>
                                        <CheckCircleOutlineRoundedIcon fontSize="small" aria-hidden="true" />
                                        <Typography variant="body2" fontWeight={600} color="success.main">
                                          Connected
                                        </Typography>
                                      </Stack>
                                    ) : isConnected ? (
                                      <Stack direction="row" spacing={0.5} alignItems="center" sx={{ color: "success.main" }}>
                                        {isAssociationPending ? <CircularProgress size={16} color="inherit" /> : <CheckCircleOutlineRoundedIcon fontSize="small" aria-hidden="true" />}
                                        <Typography variant="body2" fontWeight={600} color="success.main">
                                          {isAssociationPending ? "Associating..." : "Connected"}
                                        </Typography>
                                      </Stack>
                                    ) : (
                                      <Button
                                        size="small"
                                        variant="contained"
                                        color="primary"
                                        disabled={isAdding}
                                        onClick={() => handleAddFacebookPage(page)}
                                        startIcon={isAdding ? <CircularProgress size={16} /> : null}
                                        sx={{ borderRadius: 1.75, minWidth: 104, minHeight: 32, whiteSpace: "nowrap" }}
                                      >
                                        {isAdding ? "Adding" : "Add"}
                                      </Button>
                                    )}
                                  </Stack>
                                </Stack>
                                {pageErrors[page.id] && (
                                  <Alert
                                    severity="error"
                                    action={isAssociationFailed ? <Button color="inherit" size="small" onClick={() => retryFacebookPageAssociation(page)}>Retry association</Button> : undefined}
                                    sx={{ mt: 1.5, borderRadius: 2 }}
                                  >
                                    {pageErrors[page.id]}
                                  </Alert>
                                )}
                              </CardContent>
                            </Card>
                            );
                          }) : (
                            <Box sx={{ textAlign: "center", py: 2, px: 1.5, bgcolor: "#fff", border: "1px dashed #cbd5e1", borderRadius: 2 }}>
                              <Typography fontWeight={600}>No Pages match your search.</Typography>
                            </Box>
                          )}
                          <Button size="small" onClick={() => startOAuth("facebook")} disabled={busy || !sessionPersistenceReady} sx={{ alignSelf: "flex-start", borderRadius: 2, textTransform: "none" }}>
                            Authorize Facebook again
                          </Button>
                          {platformSpecificFlow && activePlatform === "facebook" && connectedPlatformSet.has("facebook") && (
                            <Button
                              variant="contained"
                              onClick={handleFinishFacebookPlatform}
                              disabled={busy || facebookAssociationBlocked}
                              size="small"
                              sx={{ alignSelf: { xs: "stretch", sm: "flex-end" }, borderRadius: 2, minHeight: 38, textTransform: "none" }}
                            >
                              {busy
                                ? <CircularProgress size={20} color="inherit" />
                                : "Finish Connecting"}
                            </Button>
                          )}
                        </Stack>
                      )}
                    </Box>
                  )}

                  {selectedPlatforms.includes("instagram") && showInstagramFlow && !facebookSelectionKey && (
                    <>
                      <Divider />
                      <Box>
                        <Stack direction="row" spacing={1.25} alignItems="center" justifyContent="space-between">
                          <Stack direction="row" spacing={1.25} alignItems="center">
                            <Avatar sx={{ bgcolor: "#f9eafa", color: "#b5369a", width: 40, height: 40 }}>
                              <InstagramIcon />
                            </Avatar>
                            <Box>
                              <Typography fontWeight={700}>Instagram</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {instagramAccount
                                  ? "Connected"
                                  : instagramConnectionFailed
                                    ? "Connection needs attention"
                                    : "OAuth complete · verifying profile"}
                              </Typography>
                            </Box>
                          </Stack>
                          {!instagramAccount && !instagramPreview && !instagramConnectionFailed && (
                            <Button disabled={busy || !sessionPersistenceReady} onClick={() => startOAuth("instagram")}>Authorize</Button>
                          )}
                        </Stack>
                        {instagramPreview && (
                          <Card variant="outlined" sx={{ mt: 2, borderRadius: 2.5, bgcolor: "#fff" }}>
                            <CardContent>
                              <Stack spacing={2}>
                                <Stack direction="row" spacing={1.5} alignItems="center">
                                  <Avatar src={instagramPreview.profile_image || undefined} alt="">
                                    <InstagramIcon />
                                  </Avatar>
                                  <Box>
                                    <Typography fontWeight={700}>{instagramPreview.account_name || instagramPreview.username}</Typography>
                                    <Typography variant="body2" color="text.secondary">@{instagramPreview.username}</Typography>
                                    {instagramPreview.instagram_user_id && (
                                      <Typography variant="caption" color="text.secondary">
                                        Instagram ID: {instagramPreview.instagram_user_id}
                                      </Typography>
                                    )}
                                  </Box>
                                </Stack>
                                <Typography variant="body2" color="text.secondary">
                                  {instagramConnectionFailed
                                    ? "Your profile was verified, but the connection did not finish. Retry to complete it securely."
                                    : "Your profile was verified. We’re securely completing the connection."}
                                </Typography>
                                {instagramConnectionFailed && (
                                  <Stack direction={{ xs: "column-reverse", sm: "row" }} spacing={1} justifyContent="flex-end">
                                    <Button disabled={busy} onClick={handleDeclineInstagram}>Discard preview</Button>
                                    <Button variant="contained" disabled={busy} onClick={handleConfirmInstagram} sx={{ borderRadius: 2 }}>
                                      {busy ? <CircularProgress size={20} color="inherit" /> : "Retry connection"}
                                    </Button>
                                  </Stack>
                                )}
                              </Stack>
                            </CardContent>
                          </Card>
                        )}
                        {instagramConnectionFailed && !instagramPreview && (
                          <Box sx={{ mt: 2, p: 2, border: "1px solid #fecdca", borderRadius: 2.5, bgcolor: "#fffbfa" }}>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                              The profile could not be connected yet. Retry the secure connection or discard this authorization.
                            </Typography>
                            <Stack direction={{ xs: "column-reverse", sm: "row" }} spacing={1} justifyContent="flex-end">
                              {instagramSelectionKey && (
                                <Button disabled={busy} onClick={handleDeclineInstagram}>Discard authorization</Button>
                              )}
                              <Button variant="contained" disabled={busy || !instagramSelectionKey} onClick={handleConfirmInstagram} sx={{ borderRadius: 2 }}>
                                {busy ? <CircularProgress size={20} color="inherit" /> : "Retry connection"}
                              </Button>
                            </Stack>
                          </Box>
                        )}
                        {instagramAccount && (
                          <Alert severity="success" sx={{ mt: 2 }}>
                            Connected {instagramAccount.account_name || instagramAccount.username || "Instagram account"}.
                          </Alert>
                        )}
                      </Box>
                    </>
                  )}

                  {isComplete && !isInstagramOnly && !platformSpecificFlow && selectedPlatforms.includes("facebook") && (
                    <Button variant="contained" size="large" onClick={handleFinish} disabled={busy}>
                      {busy ? <CircularProgress size={22} color="inherit" /> : "I’m done connecting"}
                    </Button>
                  )}
                  {isComplete && isInstagramOnly && busy && (
                    <Alert severity="info" sx={{ borderRadius: 2 }}>
                      Instagram is connected. We’re finishing your invitation securely…
                    </Alert>
                  )}
                  {isInstagramOnly && completionRetryNeeded && (
                    <Button variant="contained" size="large" onClick={handleFinish} disabled={busy} sx={{ borderRadius: 2 }}>
                      {busy ? <CircularProgress size={22} color="inherit" /> : "Retry completion"}
                    </Button>
                  )}
                  {!hasPersistedAccount && credentialType !== "resumption" && (
                    <Button color="inherit" onClick={handleCancel} disabled={busy}>
                      Cancel invitation session
                    </Button>
                  )}
                </Stack>
              )}

              {stage === "cancelled" && (
                <Alert severity="info">This invitation session has been cancelled. You can close this page.</Alert>
              )}

              {stage === "unavailable" && !errorMessage && (
                <Alert severity="warning">This invitation is unavailable.</Alert>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
