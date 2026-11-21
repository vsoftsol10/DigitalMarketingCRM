import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import InstagramIcon from "@mui/icons-material/Instagram";
import EmailRoundedIcon from "@mui/icons-material/EmailRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import YouTubeIcon from "@mui/icons-material/YouTube";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import LinkRoundedIcon from "@mui/icons-material/LinkRounded";
import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import LoadingState from "../../ui/LoadingState";
import ErrorState from "../../ui/ErrorState";
import EmptyState from "../../ui/EmptyState";
import LoadingSpinner from "../../ui/LoadingSpinner";
import socialAccountInvitationService from "../../../services/organization/socialAccountInvitation.service";

const platformOptions = [
  { id: "facebook", label: "Facebook Page", subtitle: "Connect Facebook Pages", icon: <FacebookRoundedIcon color="primary" /> },
  { id: "instagram", label: "Instagram Business Account", subtitle: "Connect an Instagram Business account", icon: <InstagramIcon sx={{ color: "#b33a8d" }} /> },
  { id: "linkedin", label: "LinkedIn", subtitle: "Available soon", icon: <LinkedInIcon color="disabled" />, comingSoon: true },
  { id: "youtube", label: "YouTube", subtitle: "Available soon", icon: <YouTubeIcon color="disabled" />, comingSoon: true },
];
const selectablePlatformIds = platformOptions
  .filter((platform) => !platform.comingSoon)
  .map((platform) => platform.id);

const getError = (error) =>
  error?.response?.data?.message
  || error?.response?.data?.detail
  || error?.message
  || "The invitation request could not be completed.";

const validEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

async function copyText(value) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const input = document.createElement("textarea");
  input.value = value;
  input.setAttribute("readonly", "");
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();
  const copied = document.execCommand("copy");
  document.body.removeChild(input);
  if (!copied) throw new Error("Copying the invitation link is not supported in this browser.");
}

function platformInvitationUrl(invitationUrl, platform) {
  const url = new URL(invitationUrl, window.location.origin);
  url.searchParams.set("connect", platform);
  return url.toString();
}

const statusLabel = (invitation) => {
  if (invitation.status === "revoked") return "Revoked";
  if (invitation.mode === "share_link" && invitation.has_completed_acceptance) return "Completed";
  if (invitation.status === "expired") return "Expired";
  if (invitation.status === "accepted") return "Completed";
  if (invitation.status === "exhausted") return "Used";
  if (invitation.mode === "share_link") return "Active share link";
  if (invitation.delivery_attempt_status === "pending_configuration") return "Not sent";
  if (invitation.delivery_attempt_status === "pending") return "Pending";
  if (invitation.delivery_attempt_status === "failed") return "Delivery failed";
  return "Email sent";
};

const statusChipSx = (invitation) => {
  const label = statusLabel(invitation);
  if (label === "Completed") return { bgcolor: "#dcfce7", color: "#166534" };
  if (label === "Revoked") return { bgcolor: "#fee2e2", color: "#b91c1c" };
  if (label === "Expired") return { bgcolor: "#eef1f5", color: "#475569" };
  if (label === "Active share link") return { bgcolor: "#e0edff", color: "#1d4ed8" };
  if (label === "Email sent") return { bgcolor: "#e0edff", color: "#1d4ed8" };
  return { bgcolor: "#f1f5f9", color: "#475569" };
};

export default function SocialAccountInvitationDialog({
  open,
  organization,
  organizationId,
  onClose,
}) {
  const [platforms, setPlatforms] = useState(["facebook"]);
  const [email, setEmail] = useState("");
  const [invitations, setInvitations] = useState([]);
  const [invitationsOrganizationId, setInvitationsOrganizationId] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState(null);
  const [action, setAction] = useState("");
  const [busyInvitationId, setBusyInvitationId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [sharePlatform, setSharePlatform] = useState("");
  const [shareEmail, setShareEmail] = useState("");

  const refresh = async ({ showLoading = true } = {}) => {
    if (!organizationId) return;
    if (showLoading) setLoadingList(true);
    try {
      const rows = await socialAccountInvitationService.list(organizationId);
      if (!Array.isArray(rows)) {
        throw new Error("Invitation data was not returned in the expected format.");
      }
      setInvitations(rows);
      setInvitationsOrganizationId(organizationId);
      setListError(null);
    } catch (loadError) {
      setListError(loadError);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    if (!open || !organizationId) return undefined;
    let active = true;
    socialAccountInvitationService.list(organizationId)
      .then((rows) => {
        if (!Array.isArray(rows)) {
          throw new Error("Invitation data was not returned in the expected format.");
        }
        if (active) {
          setInvitations(rows);
          setInvitationsOrganizationId(organizationId);
          setListError(null);
        }
      })
      .catch((loadError) => {
        if (active) setListError(loadError);
      })
      .finally(() => {
        if (active) setLoadingList(false);
      });
    return () => {
      active = false;
    };
  }, [open, organizationId]);

  const handleClose = () => {
    if (busy) return;
    setError("");
    setMessage("");
    setEmail("");
    onClose();
  };

  const togglePlatform = (platform) => {
    setPlatforms((current) => current.includes(platform)
      ? current.filter((item) => item !== platform)
      : [...current, platform]);
  };

  const toggleAllPlatforms = () => {
    setPlatforms((current) => selectablePlatformIds.every((platform) => current.includes(platform))
      ? []
      : selectablePlatformIds);
  };

  const createShare = async (selectedPlatforms, actionName) => {
    if (!selectedPlatforms.length || action) return;
    setAction(actionName);
    setError("");
    setMessage("");
    try {
      const created = await socialAccountInvitationService.createShareLink(organizationId, selectedPlatforms);
      if (!created?.share_url) throw new Error("The invitation link was not returned.");
      const copiedUrl = platformInvitationUrl(created.share_url, selectedPlatforms[0]);
      await copyText(copiedUrl);
      setMessage(`Invitation link copied. It expires in 72 hours.`);
      await refresh();
    } catch (requestError) {
      setError(getError(requestError));
    } finally {
      setAction("");
    }
  };

  const copyPlatformLink = (platform) => createShare([platform], `copy-${platform}`);

  const sendEmail = async () => {
    if (action || !platforms.length) return;
    if (!validEmail(email)) {
      setError("Enter a valid client email address.");
      return;
    }
    setAction("email");
    setError("");
    setMessage("");
    let invitationId = "";
    try {
      const created = await socialAccountInvitationService.createEmailInvitation(
        organizationId,
        email.trim(),
        platforms,
      );
      invitationId = created?.id;
      if (!invitationId) throw new Error("The email invitation was not created.");
      setBusyInvitationId(invitationId);
      const sent = await socialAccountInvitationService.sendEmail(organizationId, invitationId);
      setMessage(`Invitation sent to ${email.trim()}. Expires ${new Date(sent.expires_at).toLocaleString()}.`);
      setEmail("");
      await refresh();
    } catch (requestError) {
      setError(getError(requestError));
      if (invitationId) {
        setMessage("The invitation record was created. Use Retry to continue the delivery without invalidating an active link.");
        await refresh();
      }
    } finally {
      setBusyInvitationId("");
      setAction("");
    }
  };

  const sendPlatformEmail = async () => {
    if (action || !sharePlatform) return;
    if (!validEmail(shareEmail)) {
      setError("Enter a valid client email address.");
      return;
    }
    setAction(`email-${sharePlatform}`);
    setError("");
    setMessage("");
    let invitationId = "";
    try {
      const created = await socialAccountInvitationService.createEmailInvitation(
        organizationId,
        shareEmail.trim(),
        [sharePlatform],
      );
      invitationId = created?.id;
      if (!invitationId) throw new Error("The email invitation was not created.");
      await socialAccountInvitationService.sendEmail(organizationId, invitationId);
      setMessage(`${platformOptions.find((option) => option.id === sharePlatform)?.label} invitation sent to ${shareEmail.trim()}.`);
      setShareEmail("");
      setSharePlatform("");
      await refresh();
    } catch (requestError) {
      setError(getError(requestError));
      if (invitationId) {
        setMessage("The invitation record was created. Use Retry in the invitation list to continue delivery.");
        await refresh();
      }
    } finally {
      setAction("");
    }
  };

  const runInvitationAction = async (invitation, kind) => {
    if (action || busyInvitationId) return;
    setBusyInvitationId(invitation.id);
    setError("");
    setMessage("");
    try {
      if (kind === "send") {
        await socialAccountInvitationService.sendEmail(organizationId, invitation.id);
        setMessage("Invitation email sent.");
      } else if (kind === "retry") {
        await socialAccountInvitationService.retryEmail(organizationId, invitation.id);
        setMessage("Invitation email sent.");
      } else if (kind === "resend") {
        await socialAccountInvitationService.resendEmail(organizationId, invitation.id);
        setMessage("A replacement invitation link was sent.");
      } else {
        await socialAccountInvitationService.revoke(organizationId, invitation.id);
        setMessage("Invitation revoked.");
      }
      await refresh();
    } catch (requestError) {
      setError(getError(requestError));
      await refresh();
    } finally {
      setBusyInvitationId("");
    }
  };

  const busy = Boolean(action || busyInvitationId);
  const hasLoadedInvitations = Boolean(
    organizationId && invitationsOrganizationId === organizationId,
  );
  const visibleInvitations = hasLoadedInvitations ? invitations : [];
  const listLoading = loadingList || Boolean(
    open && organizationId && !hasLoadedInvitations && !listError,
  );
  const allPlatformsSelected = selectablePlatformIds.every((platform) => platforms.includes(platform));
  const somePlatformsSelected = platforms.length > 0 && !allPlatformsSelected;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth={false}
      scroll="paper"
      sx={{
        "& .MuiDialog-paper": {
          boxSizing: "border-box",
          width: { xs: "calc(100vw - 24px)", sm: "min(1000px, calc(100vw - 32px))" },
          minWidth: { xs: "calc(100vw - 24px)", sm: "min(1000px, calc(100vw - 32px))" },
          maxWidth: { xs: "calc(100vw - 24px)", sm: 1000 },
          height: { xs: "90vh", sm: "82vh" },
          maxHeight: { xs: "90vh", sm: "82vh" },
          flex: "0 0 auto",
        },
      }}
      PaperProps={{
        sx: {
          m: { xs: 1.5, sm: 2 },
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          borderRadius: "20px",
          border: "1px solid #DDE3F1",
          boxShadow: "0 16px 36px rgba(31,41,80,.16)",
          bgcolor: "#fff",
        },
      }}
    >
      <DialogTitle sx={{ position: "relative", flexShrink: 0, px: { xs: 2, sm: 2.75 }, py: { xs: 1.5, sm: 2 }, pr: 8, borderBottom: "1px solid #E5E9F1", bgcolor: "#FFFFFF" }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1.5} sx={{ minWidth: 0 }}>
          <Typography component="h2" sx={{ minWidth: 0, flex: 1, fontSize: { xs: 20, sm: 24 }, fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1.2, color: "#172554" }}>
            Invite Social Accounts
          </Typography>
          <Chip
            icon={<AccessTimeRoundedIcon sx={{ fontSize: 18 }} />}
            label="Expires in 72 hours"
            size="small"
            sx={{ flexShrink: 0, height: 30, borderRadius: "10px", px: 0.75, bgcolor: "#F1F5F9", color: "#475569", fontSize: { xs: 11, sm: 13 }, fontWeight: 600, "& .MuiChip-icon": { color: "#64748B" } }}
          />
        </Stack>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 0.75, lineHeight: 1.4, fontSize: { xs: 13, sm: 15 } }}>
          Copy a platform link or send an invitation by email to invite them to connect.
        </Typography>
        <IconButton
          aria-label="Close invitation dialog"
          onClick={handleClose}
          disabled={busy}
          sx={{ position: "absolute", top: 10, right: { xs: 10, sm: 14 }, width: 34, height: 34, color: "#6b7280", "&:hover": { bgcolor: "#f3f4f6" } }}
        >
          <CloseRoundedIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ flex: "1 1 auto", width: "100%", minWidth: 0, minHeight: 0, overflowY: "auto", p: 0, bgcolor: "#F8FAFC", scrollbarGutter: "stable" }}>
        <Box sx={{ width: "100%", minWidth: 0, px: { xs: 1.5, sm: 2.75 }, py: { xs: 1.25, sm: 2 } }}>
          <Stack spacing={1.5}>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }, gap: { xs: 1, sm: 1.25 } }}>
              {platformOptions.map((platform) => {
                const selected = !platform.comingSoon && platforms.includes(platform.id);
                const active = !platform.comingSoon;
                const cardBackground = "#FFFFFF";
                const accent = platform.id === "instagram" ? "#c13584" : "#1877f2";
                return (
                  <Card
                    key={platform.id}
                    variant="outlined"
                    onClick={() => { if (active && !busy) togglePlatform(platform.id); }}
                    sx={{
                      position: "relative",
                      height: { xs: 142, sm: 150 },
                      borderRadius: "14px",
                      borderColor: selected ? accent : "#dce2eb",
                      bgcolor: cardBackground,
                      boxShadow: "none",
                      opacity: active ? 1 : 0.72,
                      cursor: active && !busy ? "pointer" : "default",
                      transition: "border-color 150ms ease, box-shadow 150ms ease",
                      "&:hover": active && !busy ? { borderColor: accent, boxShadow: "0 3px 8px rgba(31,41,80,.06)" } : undefined,
                    }}
                  >
                    <Checkbox
                      checked={selected}
                      disabled={!active || busy}
                      onChange={() => togglePlatform(platform.id)}
                      onClick={(event) => event.stopPropagation()}
                      inputProps={{ "aria-label": `Select ${platform.label}` }}
                      size="small"
                      sx={{ position: "absolute", top: 9, left: 9, zIndex: 1, p: 0.35, "& .MuiSvgIcon-root": { fontSize: 22 } }}
                    />
                    <CardContent sx={{ height: "100%", boxSizing: "border-box", p: { xs: 1.5, sm: 1.75 }, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", "&:last-child": { pb: { xs: 1.5, sm: 1.75 } } }}>
                      <Box sx={{ width: 52, height: 52, flexShrink: 0, display: "grid", placeItems: "center", borderRadius: "50%", bgcolor: platform.id === "facebook" ? "#1877f2" : platform.id === "instagram" ? "#fff" : "#d5dbe5", background: platform.id === "instagram" ? "linear-gradient(135deg, #feda75 0%, #d62976 55%, #4f5bd5 100%)" : undefined, color: active ? accent : "#7b8490", boxShadow: active ? "0 2px 5px rgba(15, 23, 42, 0.12)" : "none", "& svg": { fontSize: 32, color: active ? "#fff" : undefined } }}>
                          {platform.icon}
                      </Box>
                      <Typography variant="subtitle1" sx={{ mt: 0.75, fontSize: { xs: 14, sm: 15 }, fontWeight: 700, lineHeight: 1.2, textAlign: "center", color: active ? "#111827" : "#64748b", overflowWrap: "anywhere" }}>
                            {platform.label}
                      </Typography>
                      {platform.comingSoon ? (
                        <Chip size="small" label="Coming soon" sx={{ mt: 0.75, height: 24, borderRadius: 2, bgcolor: "#e2e7ef", color: "#475569", fontSize: 11.5, fontWeight: 600 }} />
                      ) : (
                        <Stack direction="row" alignItems="center" spacing={0.75} sx={{ mt: 0.65 }}>
                          <Button size="small" variant="text" startIcon={<LinkRoundedIcon />} disabled={busy} onClick={(event) => { event.stopPropagation(); copyPlatformLink(platform.id); }} sx={{ minWidth: 0, px: 0.5, py: 0.2, minHeight: 25, borderRadius: 0.75, color: "#075be7", textTransform: "none", fontSize: 13, fontWeight: 700, "& .MuiButton-startIcon": { mr: 0.3, "& svg": { fontSize: 17 } }, "&:hover": { bgcolor: "rgba(255,255,255,0.65)" } }}>
                            Copy
                          </Button>
                          <Divider orientation="vertical" flexItem sx={{ my: 0.35, borderColor: "#9aa7ba" }} />
                          <Button size="small" variant="text" startIcon={<EmailRoundedIcon />} disabled={busy} onClick={(event) => { event.stopPropagation(); setSharePlatform(platform.id); setError(""); }} sx={{ minWidth: 0, px: 0.5, py: 0.2, minHeight: 25, borderRadius: 0.75, color: "#075be7", textTransform: "none", fontSize: 13, fontWeight: 700, "& .MuiButton-startIcon": { mr: 0.3, "& svg": { fontSize: 17 } }, "&:hover": { bgcolor: "rgba(255,255,255,0.65)" } }}>
                            Share
                          </Button>
                        </Stack>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </Box>

            {error && <Alert severity="error">{error}</Alert>}
            {message && <Alert severity="success">{message}</Alert>}
            <Divider sx={{ borderColor: "#E5E9F1", my: 0.25 }} />

            <Box sx={{ minHeight: { xs: 190, sm: 230 } }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 0.75 }}>
                <Typography variant="subtitle1" sx={{ fontSize: { xs: 17, sm: 18 }, fontWeight: 700, lineHeight: 1.3, color: "#172554" }}>Recent Invitations</Typography>
              </Stack>
              <Box>
                {listLoading && visibleInvitations.length === 0 && (
                  <LoadingState
                    label="LOADING INVITATIONS..."
                    variant="container"
                    minHeight={190}
                  />
                )}
                {listError && visibleInvitations.length === 0 && (
                  <ErrorState
                    title={hasLoadedInvitations ? "Unable to refresh invitations" : "Unable to load invitations"}
                    message={listError}
                    onRetry={listLoading ? undefined : () => refresh()}
                    variant="container"
                    sx={{ minHeight: 190 }}
                  />
                )}
                {listError && visibleInvitations.length > 0 && (
                  <ErrorState
                    title="Unable to refresh invitations"
                    message={listError}
                    onRetry={listLoading ? undefined : () => refresh()}
                    variant="inline"
                  />
                )}
                {listLoading && visibleInvitations.length > 0 && (
                  <LoadingState label="REFRESHING INVITATIONS..." variant="inline" />
                )}
                {hasLoadedInvitations && !listLoading && !listError && visibleInvitations.length === 0 && (
                  <EmptyState
                    title="No invitations yet"
                    description="Invitations for this organization will appear here."
                    sx={{ minHeight: 190 }}
                  />
                )}
                {hasLoadedInvitations && visibleInvitations.length > 0 && (
                  <TableContainer sx={{ width: "100%", minWidth: 0, border: "1px solid #e1e5ea", borderRadius: 1.25, bgcolor: "#fff", overflowX: "auto" }}>
                    <Table size="small" sx={{ minWidth: 680 }}>
                      <TableHead>
                        <TableRow sx={{ bgcolor: "#eef1f6" }}>
                          {['Recipient', 'Platforms', 'Status', 'Expires', 'Actions'].map((heading) => (
                            <TableCell key={heading} sx={{ py: 0.8, px: 1.25, borderBottom: "1px solid #e1e5ea", color: "#334155", fontSize: 12.5, fontWeight: 700, whiteSpace: "nowrap" }}>
                              {heading}
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {visibleInvitations.map((invitation) => (
                          <TableRow key={invitation.id} hover sx={{ "&:last-child td": { borderBottom: 0 } }}>
                            <TableCell sx={{ py: 0.8, px: 1.25, maxWidth: 250, color: "#1f2937", fontSize: 13, fontWeight: 600, overflowWrap: "anywhere" }}>
                              {invitation.recipient_email || "Share link"}
                            </TableCell>
                            <TableCell sx={{ py: 0.8, px: 1.25 }}>
                              <Stack direction="row" spacing={0.35} alignItems="center">
                                {invitation.platforms?.map((platform) => {
                                  const option = platformOptions.find((item) => item.id === platform);
                                  if (!option) return null;
                                  return <Box key={platform} aria-label={option.label} sx={{ width: 25, height: 25, display: "grid", placeItems: "center", borderRadius: "50%", bgcolor: platform === "facebook" ? "#1877f2" : "#fff", background: platform === "instagram" ? "linear-gradient(135deg, #feda75 0%, #d62976 55%, #4f5bd5 100%)" : undefined, "& svg": { fontSize: 21, color: platform === "facebook" || platform === "instagram" ? "#fff" : undefined } }}>{option.icon}</Box>;
                                })}
                              </Stack>
                            </TableCell>
                            <TableCell sx={{ py: 0.8, px: 1.25 }}>
                              <Chip label={statusLabel(invitation)} size="small" sx={{ height: 26, borderRadius: 2, px: 0.5, fontSize: 11.5, fontWeight: 700, ...statusChipSx(invitation) }} />
                            </TableCell>
                            <TableCell sx={{ py: 0.8, px: 1.25, color: "#334155", fontSize: 12.5, whiteSpace: "nowrap" }}>
                              {new Date(invitation.expires_at).toLocaleString()}
                            </TableCell>
                            <TableCell sx={{ py: 0.8, px: 1.25 }}>
                              <Stack direction="row" spacing={0.15} alignItems="center" flexWrap="nowrap">
                                {invitation.send_available && <Button size="small" disabled={busy} onClick={() => runInvitationAction(invitation, "send")} sx={{ minWidth: 0, px: 0.65, py: 0.2, fontSize: 12, whiteSpace: "nowrap", textTransform: "none", color: "#145be7" }}>Send</Button>}
                                {invitation.retry_available && <Button size="small" disabled={busy} onClick={() => runInvitationAction(invitation, "retry")} sx={{ minWidth: 0, px: 0.65, py: 0.2, fontSize: 12, whiteSpace: "nowrap", textTransform: "none", color: "#145be7" }}>Retry</Button>}
                                {invitation.resend_available && <Button size="small" disabled={busy} onClick={() => runInvitationAction(invitation, "resend")} sx={{ minWidth: 0, px: 0.65, py: 0.2, fontSize: 12, whiteSpace: "nowrap", textTransform: "none", color: "#145be7" }}>Resend</Button>}
                                {invitation.revoke_available && <Button size="small" color="error" disabled={busy} onClick={() => runInvitationAction(invitation, "revoke")} sx={{ minWidth: 0, px: 0.65, py: 0.2, fontSize: 12, whiteSpace: "nowrap", textTransform: "none" }}>Revoke</Button>}
                                {!invitation.send_available && !invitation.retry_available && !invitation.resend_available && !invitation.revoke_available && <Typography variant="body2" color="text.secondary">—</Typography>}
                              </Stack>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Box>
            </Box>
          </Stack>
        </Box>
      </DialogContent>

      <DialogActions sx={{ flexShrink: 0, p: { xs: 1.25, sm: 2 }, borderTop: "1px solid #E5E9F1", bgcolor: "#FFFFFF" }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={{ xs: 0.75, sm: 1.5 }} alignItems={{ xs: "stretch", sm: "center" }} sx={{ width: "100%" }}>
          <FormControlLabel
            sx={{ m: 0, flexShrink: 0, "& .MuiCheckbox-root": { p: 0.3 }, "& .MuiTypography-root": { fontSize: 14, fontWeight: 600, color: "#1f2937" }, "& .MuiSvgIcon-root": { fontSize: 22 } }}
            control={(
              <Checkbox checked={allPlatformsSelected} indeterminate={somePlatformsSelected} disabled={busy} onChange={toggleAllPlatforms} inputProps={{ "aria-label": "Select all supported platforms" }} />
            )}
            label="Select all"
          />
          <TextField
            type="email"
            fullWidth
            placeholder="client@email.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            disabled={busy}
            autoComplete="email"
            inputProps={{ maxLength: 254 }}
            sx={{ flex: 1, "& .MuiOutlinedInput-root": { height: 44, borderRadius: "12px", bgcolor: "#fff", "& fieldset": { borderColor: "#DCE2EF" }, "&:hover fieldset": { borderColor: "#B8C3D8" }, "&.Mui-focused fieldset": { borderColor: "#7B61E8" } }, "& input": { py: 0.85, fontSize: 14 } }}
          />
          <Button
            variant="contained"
            startIcon={action === "email" ? <LoadingSpinner size={17} color="inherit" decorative /> : <EmailRoundedIcon />}
            disabled={busy || !platforms.length}
            onClick={sendEmail}
            sx={{ minHeight: 44, minWidth: { sm: 190 }, width: { xs: "100%", sm: "auto" }, whiteSpace: "nowrap", borderRadius: "12px", textTransform: "none", fontSize: 14, fontWeight: 700, background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)", boxShadow: "none", "&:hover": { background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)", boxShadow: "none" } }}
          >
            Send Invitations
          </Button>
        </Stack>
      </DialogActions>
      <Dialog open={Boolean(sharePlatform)} onClose={() => { if (!busy) { setSharePlatform(""); setShareEmail(""); } }} fullWidth maxWidth="xs" PaperProps={{ sx: { borderRadius: "18px", border: "1px solid #DDE3F1", boxShadow: "0 16px 36px rgba(31,41,80,.16)" } }}>
        <DialogTitle sx={{ color: "#172554", fontWeight: 700, borderBottom: "1px solid #E5E9F1" }}>Share {platformOptions.find((option) => option.id === sharePlatform)?.label} invitation</DialogTitle>
        <DialogContent sx={{ bgcolor: "#FFFFFF", pt: 2 }}>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Send a platform-specific invitation for {organization?.name || "this organization"}.
            </Typography>
            <TextField
              label="Client email"
              type="email"
              value={shareEmail}
              onChange={(event) => setShareEmail(event.target.value)}
              autoComplete="email"
              inputProps={{ maxLength: 254 }}
              disabled={busy}
              fullWidth
            />
            {error && <Alert severity="error">{error}</Alert>}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ borderTop: "1px solid #E5E9F1", p: 2, bgcolor: "#FFFFFF" }}>
          <Button onClick={() => { setSharePlatform(""); setShareEmail(""); }} disabled={busy} sx={{ color: "#475569", textTransform: "none" }}>Cancel</Button>
          <Button variant="contained" onClick={sendPlatformEmail} disabled={busy || !sharePlatform} sx={{ borderRadius: "12px", px: 2, textTransform: "none", background: "linear-gradient(110deg, #8B4BF5 0%, #3977F6 100%)", boxShadow: "none", "&:hover": { background: "linear-gradient(110deg, #7D3CEB 0%, #2F6EEA 100%)", boxShadow: "none" } }}>
            {action === `email-${sharePlatform}` ? <LoadingSpinner size={18} color="inherit" decorative /> : "Send invitation"}
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
}
