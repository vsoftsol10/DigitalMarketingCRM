import { useEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";
import {
  Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle,
  IconButton, Stack, Table, TableBody, TableCell, TableHead, TableRow,
  TextField, Typography,
} from "@mui/material";
import AddCircleOutlinedIcon from "@mui/icons-material/AddCircleOutlined";
import CheckRoundedIcon from "@mui/icons-material/CheckRounded";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import CloseIcon from "@mui/icons-material/Close";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import ReportDocument from "./ReportDocument";
import reportsService from "../../services/reports.service";
import {
  insightsAlertSx,
  insightsGlassSurfaceSx,
  insightsPrimaryButtonSx,
  insightsSecondaryButtonSx,
} from "../insights/insightsGlassSx";

const REPORT_WIDTH = 1200;
const REPORT_HEIGHT = 760;
const REPORT_PIXEL_RATIO = 2;

function getErrorMessage(error) {
  const data = error?.response?.data;
  if (data instanceof Blob) return "The report could not be generated. Please try again.";
  return data?.message || data?.detail || data?.errors?.date_range || data?.errors?.render
    || error?.message || "The report could not be generated. Please try again.";
}

async function renderReportPng(report) {
  const { toBlob } = await import("html-to-image");
  const mount = document.createElement("div");
  mount.setAttribute("aria-hidden", "true");
  Object.assign(mount.style, {
    position: "fixed",
    left: "-10000px",
    top: "0",
    width: `${REPORT_WIDTH}px`,
    height: `${REPORT_HEIGHT}px`,
    overflow: "hidden",
    pointerEvents: "none",
    zIndex: "-1",
  });
  document.body.appendChild(mount);

  const root = createRoot(mount);
  try {
    flushSync(() => root.render(<ReportDocument report={report} />));
    const node = mount.querySelector("#report-document");
    if (!node) throw new Error("The report document could not be prepared.");

    if (document.fonts?.ready) await document.fonts.ready;
    await Promise.all(Array.from(node.querySelectorAll("img"), async (image) => {
      if (!image.complete) {
        await new Promise((resolve, reject) => {
          image.addEventListener("load", resolve, { once: true });
          image.addEventListener("error", () => reject(new Error("A report image could not be loaded.")), { once: true });
        });
      }
      if (!image.naturalWidth) throw new Error("A report image could not be loaded.");
      if (typeof image.decode === "function") await image.decode();
    }));
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));

    const bounds = node.getBoundingClientRect();
    if (Math.round(bounds.width) !== REPORT_WIDTH || Math.round(bounds.height) !== REPORT_HEIGHT) {
      throw new Error("The report layout has unexpected dimensions.");
    }

    const blob = await toBlob(node, {
      width: REPORT_WIDTH,
      height: REPORT_HEIGHT,
      pixelRatio: REPORT_PIXEL_RATIO,
      backgroundColor: "#fff",
    });
    if (!blob || blob.type !== "image/png") throw new Error("The report image could not be generated.");
    return blob;
  } finally {
    root.unmount();
    mount.remove();
  }
}

export default function InsightsExportDialog({ open, mode, scope, organization, account, onClose }) {
  const [previewRecord, setPreviewRecord] = useState(null);
  const [adsRows, setAdsRows] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [errorRecord, setErrorRecord] = useState(null);
  const [imageUrl, setImageUrl] = useState("");
  const [viewerOpen, setViewerOpen] = useState(false);
  const adsDialogOpened = useRef(false);
  const requestKey = `${organization?.id || ""}/${account?.id || ""}/${scope?.since || ""}/${scope?.until || ""}/${mode}`;
  const preview = previewRecord?.key === requestKey ? previewRecord.value : null;
  const error = errorRecord?.key === requestKey ? errorRecord.message : "";
  const loadingPreview = open && !preview && !error;

  useEffect(() => {
    if (!open || !scope || !organization || !account) return undefined;
    let current = true;
    reportsService.preview({
      organization_id: organization.id,
      social_account_id: account.id,
      platform: scope.platform,
      since: scope.since,
      until: scope.until,
      mode,
      meta_ads: [],
    }).then((result) => { if (current) setPreviewRecord({ key: requestKey, value: result }); })
      .catch((requestError) => { if (current) setErrorRecord({ key: requestKey, message: getErrorMessage(requestError) }); });
    return () => { current = false; };
  }, [account, mode, open, organization, requestKey, scope]);

  useEffect(() => {
    if (!open || mode !== "add_ads") {
      adsDialogOpened.current = false;
      return;
    }
    if (!adsDialogOpened.current) {
      adsDialogOpened.current = true;
      setAdsRows([{ date: "", total_leads: "" }]);
    }
  }, [mode, open]);

  useEffect(() => () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
  }, [imageUrl]);

  const adsValidation = useMemo(() => adsRows.map((row) => {
    const dateValid = Boolean(row.date);
    const leads = row.total_leads.trim();
    const leadsValid = leads !== "" && Number.isFinite(Number(leads)) && Number(leads) >= 0;
    return { dateValid, leadsValid };
  }), [adsRows]);
  const adsValid = adsValidation.every((row) => row.dateValid && row.leadsValid);

  function updateAdsRow(index, field, value) {
    setAdsRows((rows) => rows.map((row, rowIndex) => rowIndex === index ? { ...row, [field]: value } : row));
  }

  async function generateReport() {
    if (!preview || !scope || !organization || !account || !adsValid) return;
    setGenerating(true);
    try {
      const response = mode === "current" ? preview : await reportsService.preview({
        organization_id: organization.id,
        social_account_id: account.id,
        platform: scope.platform,
        since: scope.since,
        until: scope.until,
        mode,
        meta_ads: adsRows.map((row) => ({ date: row.date, total_leads: row.total_leads })),
      });
      const png = await renderReportPng(response.report);
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      setImageUrl(URL.createObjectURL(png));
      setViewerOpen(true);
      setPreviewRecord({ key: requestKey, value: response });
    } catch (requestError) {
      setErrorRecord({ key: requestKey, message: getErrorMessage(requestError) });
    } finally {
      setGenerating(false);
    }
  }

  const report = preview?.report;
  const exportComplete = Boolean(report && !loadingPreview && !generating);
  const accountLabel = account?.username || account?.account_name || "selected account";
  const organizationLabel = organization?.name || "selected organization";
  const platformLabel = scope?.platform ? `${scope.platform[0].toUpperCase()}${scope.platform.slice(1)}` : "selected platform";
  const durationLabel = {
    "7D": "Last 7 Days",
    "28D": "Last 28 Days",
    "30D": "Last 30 Days",
  }[scope?.duration] || "selected duration";
  const includedItems = [
    "Total Reach",
    "Total Engagement",
    "Total Followers",
    "Total Views",
    "Total Posts",
    "Daily Performance",
    "Content Performance",
    ...(mode === "add_ads" ? ["Meta Ads"] : []),
  ];

  return <>
    <Dialog
      open={open}
      onClose={generating ? undefined : () => { setAdsRows([]); onClose(); }}
      fullWidth
      maxWidth="md"
      sx={{
        "& .MuiDialog-paper": {
          width: { xs: "calc(100% - 24px)", sm: "calc(100% - 48px)" },
          maxWidth: 540,
          maxHeight: "min(90vh, 900px)",
          ...insightsGlassSurfaceSx,
          borderRadius: "20px",
          boxShadow: "0 16px 36px rgba(31,41,80,.16)",
          overflow: "hidden",
        },
      }}
    >
      <DialogTitle sx={{ px: { xs: 2, sm: 3 }, py: 2.25, pr: 7, color: "#172554", background: "#FFFFFF", borderBottom: "1px solid #E5E9F1" }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <Box sx={{ width: 40, height: 40, flex: "0 0 auto", borderRadius: "11px", display: "grid", placeItems: "center", background: "#F3F0FF", color: "#6941D9", border: "1px solid #E7E1FF" }}>
            <DownloadOutlinedIcon sx={{ fontSize: 23 }} />
          </Box>
          <Box sx={{ minWidth: 0, pt: 0.1 }}>
            <Typography component="div" sx={{ color: "#172554", fontSize: { xs: 18, sm: 20 }, fontWeight: 700, lineHeight: 1.3 }}>
              {mode === "add_ads" ? "Add Data & Export" : "Export Current Data"}
            </Typography>
            <Typography sx={{ mt: 0.75, color: "#667792", fontSize: 14, lineHeight: 1.55, fontWeight: 400 }}>
              Export currently available CRM data for {organizationLabel}, {accountLabel} ({platformLabel}), and {durationLabel}.
            </Typography>
          </Box>
        </Stack>
        <IconButton aria-label="Close export dialog" onClick={() => { setAdsRows([]); onClose(); }} disabled={generating} sx={{ position: "absolute", right: 12, top: 12, width: 38, height: 38, color: "#64748B", border: "1px solid #D8DEEA", borderRadius: "10px", background: "#FFFFFF", "&:hover": { background: "#F8FAFC" } }}><CloseIcon /></IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ px: { xs: 2, sm: 3 }, py: 2.25, borderColor: "#E5E9F1", background: "#FFFFFF", overflowY: "auto", overflowX: "hidden" }}>
        <Stack spacing={2}>
          <Box sx={{ minHeight: 132, px: 2, py: 1.75, border: "1px solid #E5E9F1", borderRadius: "14px", background: "#F8FAFC", boxShadow: "none", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center" }}>
            <Box sx={{ width: 44, height: 44, mb: 0.75, borderRadius: "11px", display: "grid", placeItems: "center", background: "#ECFDF3", color: "#039855", border: "1px solid #D1FADF" }}>
              <CheckRoundedIcon sx={{ fontSize: 32 }} />
            </Box>
            <Typography sx={{ color: "#172B4D", fontSize: 14, lineHeight: 1.5, fontWeight: 700 }}>
              {exportComplete ? "Completed" : "Exporting..."}
            </Typography>
            <Typography sx={{ mt: 0.25, color: "#667792", fontSize: 12.5, lineHeight: 1.5 }}>
              {exportComplete ? "Your report is ready to generate." : "Your file will be downloaded shortly."}
            </Typography>
          </Box>

          <Box>
            <Stack direction="row" spacing={1.25} alignItems="center" sx={{ mb: 0.75 }}>
              <Box sx={{ width: 24, height: 24, flex: "0 0 auto", borderRadius: "8px", display: "grid", placeItems: "center", background: "#F3F0FF", color: "#6941D9", border: "1px solid #E7E1FF" }}>
                <InfoOutlinedIcon sx={{ fontSize: 14 }} />
              </Box>
              <Typography sx={{ color: "#172B4D", fontSize: 14, fontWeight: 700 }}>This report includes</Typography>
            </Stack>
            <Box component="ul" sx={{ m: 0, pl: 5.5, color: "#667792", fontSize: 13, lineHeight: 1.75, "& li::marker": { color: "#7B61E8" } }}>
              {includedItems.map((item) => <Box component="li" key={item} sx={{ pl: 0.25 }}>{item}</Box>)}
            </Box>
          </Box>

          {error && <Alert severity="error" sx={insightsAlertSx}>{error}</Alert>}

          {mode === "add_ads" && <Box sx={{ pt: 1.5, borderTop: "1px solid #E5E9F1" }}>
            <Typography variant="subtitle2" fontWeight={700} mb={1} sx={{ color: "#172B4D" }}>Meta Ads (optional, up to 5 rows)</Typography>
            <Box sx={{ width: "100%", overflowX: "hidden", border: "1px solid #E1E6F0", borderRadius: "12px", overflow: "hidden", background: "#FFFFFF", boxShadow: "none" }}>
              <Table
                size="small"
                sx={{
                  width: "100%",
                  tableLayout: "fixed",
                  borderCollapse: "separate",
                  borderSpacing: 0,
                  m: 0,
                  "& .MuiTableCell-root": { px: { xs: 0.5, sm: 1 }, borderBottom: "1px solid #E5E9F1", borderRight: "1px solid #EEF1F6" },
                  "& .MuiTableCell-root:last-child": { borderRight: 0 },
                  "& .MuiTableHead .MuiTableCell-root": { py: 0.9, color: "#475569", background: "#F8FAFC", fontSize: 12, lineHeight: 1.4, fontWeight: 700 },
                  "& .MuiTableBody .MuiTableCell-root": { py: 0.65, verticalAlign: "middle", bgcolor: "#FFFFFF" },
                  "& .MuiTableBody .MuiTableRow:last-child .MuiTableCell-root": { borderBottom: 0 },
                }}
              >
                <colgroup>
                  <col style={{ width: "42%" }} />
                  <col style={{ width: "42%" }} />
                  <col style={{ width: "16%" }} />
                </colgroup>
                <TableHead><TableRow><TableCell>Date</TableCell><TableCell>Total Leads</TableCell><TableCell align="center">Remove</TableCell></TableRow></TableHead>
                <TableBody>{adsRows.map((row, index) => <TableRow key={index}>
                  <TableCell>
                    <TextField
                      fullWidth
                      type="date"
                      size="small"
                      value={row.date}
                      onChange={(event) => updateAdsRow(index, "date", event.target.value)}
                      error={!adsValidation[index].dateValid}
                      helperText={!adsValidation[index].dateValid ? "Date is required" : " "}
                      InputLabelProps={{ shrink: true }}
                      inputProps={{ "aria-label": `Meta Ads date ${index + 1}` }}
                      sx={{
                        minWidth: 0,
                        "& .MuiOutlinedInput-root": { height: 34, borderRadius: 0, bgcolor: "transparent", px: 0.25, boxShadow: "none", "& fieldset": { border: 0 }, "&.Mui-focused": { boxShadow: "inset 0 -1px #7B61E8" }, "&.Mui-error": { boxShadow: "inset 0 -1px #DC2626" } },
                        "& .MuiInputBase-input": { minWidth: 0, px: 0.75, fontSize: 12, color: "#334155" },
                        "& .MuiFormHelperText-root": { minHeight: 18, mx: 0, mt: 0.5, lineHeight: "18px", whiteSpace: "nowrap", fontSize: 10.5 },
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      fullWidth
                      type="number"
                      size="small"
                      value={row.total_leads}
                      onChange={(event) => updateAdsRow(index, "total_leads", event.target.value)}
                      error={!adsValidation[index].leadsValid}
                      helperText={!adsValidation[index].leadsValid ? "Enter a non-negative number" : " "}
                      inputProps={{ min: 0, step: "any", "aria-label": `Total leads ${index + 1}` }}
                      sx={{
                        minWidth: 0,
                        "& .MuiOutlinedInput-root": { height: 34, borderRadius: 0, bgcolor: "transparent", px: 0.25, boxShadow: "none", "& fieldset": { border: 0 }, "&.Mui-focused": { boxShadow: "inset 0 -1px #7B61E8" }, "&.Mui-error": { boxShadow: "inset 0 -1px #DC2626" } },
                        "& .MuiInputBase-input": { minWidth: 0, px: 0.75, fontSize: 12, color: "#334155" },
                        "& .MuiFormHelperText-root": { minHeight: 18, mx: 0, mt: 0.5, lineHeight: "18px", whiteSpace: "nowrap", fontSize: 10.5 },
                      }}
                    />
                  </TableCell>
                  <TableCell align="center" sx={{ px: 0.25 }}>
                    <IconButton aria-label={`Remove Meta Ads row ${index + 1}`} onClick={() => setAdsRows((rows) => rows.filter((_, rowIndex) => rowIndex !== index))} sx={{ mt: 0.25, color: "#64748B", borderRadius: "9px", "&:hover": { color: "#C93248", background: "#FFF7F8" } }}><DeleteOutlinedIcon /></IconButton>
                  </TableCell>
                </TableRow>)}</TableBody>
              </Table>
            </Box>
            {adsRows.length < 5 && <Button startIcon={<AddCircleOutlinedIcon />} onClick={() => setAdsRows((rows) => [...rows, { date: "", total_leads: "" }])} sx={{ ...insightsSecondaryButtonSx, mt: 0.75 }}>Add More Data</Button>}
          </Box>}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: 1.75, borderTop: "1px solid #E5E9F1", background: "#FFFFFF", gap: 1 }}>
        <Button onClick={() => { setAdsRows([]); onClose(); }} disabled={generating} sx={insightsSecondaryButtonSx}>Cancel</Button>
        <Button variant="contained" onClick={generateReport} disabled={!exportComplete || !adsValid} sx={{ ...insightsPrimaryButtonSx, px: 2.25, py: 1 }}>
          {generating ? "Generating…" : "Generate Report"}
        </Button>
      </DialogActions>
    </Dialog>
    <Dialog
      open={viewerOpen}
      onClose={() => setViewerOpen(false)}
      fullWidth
      maxWidth="xl"
      sx={{
        "& .MuiDialog-paper": {
          width: { xs: "calc(100vw - 24px)", sm: "calc(100vw - 48px)" },
          height: { xs: "calc(100dvh - 24px)", sm: "calc(100dvh - 48px)" },
          maxWidth: "min(1536px, calc(100vw - 48px))",
          maxHeight: "calc(100dvh - 24px)",
          display: "flex",
          flexDirection: "column",
          ...insightsGlassSurfaceSx,
          borderRadius: "20px",
          boxShadow: "0 16px 36px rgba(31,41,80,.16)",
        },
      }}
    >
      <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", color: "#172554", background: "#FFFFFF", borderBottom: "1px solid #E5E9F1" }}>
        Report Preview
        <IconButton aria-label="Close report preview" onClick={() => setViewerOpen(false)} sx={{ width: 38, height: 38, color: "#64748B", border: "1px solid #D8DEEA", borderRadius: "10px", background: "#FFFFFF", "&:hover": { background: "#F8FAFC" } }}><CloseIcon /></IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ flex: "1 1 auto", minHeight: 0, display: "flex", overflow: "hidden", p: { xs: 1, sm: 2 }, borderColor: "#E5E9F1", background: "#F8FAFC" }}><Box sx={{ width: "100%", height: "100%", minHeight: 0, overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid #E1E6F0", borderRadius: "14px", background: "#FFFFFF", boxShadow: "none" }}>
        {imageUrl && <img src={imageUrl} alt="Generated Insights report" style={{ display: "block", width: "auto", height: "auto", maxWidth: "100%", maxHeight: "100%", objectFit: "contain", margin: "0 auto", boxShadow: "0 3px 16px #182b4a22" }} />}
      </Box></DialogContent>
      <DialogActions sx={{ p: 2, borderTop: "1px solid #E5E9F1", background: "#FFFFFF" }}>
        <Button component="a" href={imageUrl || undefined} download="insights-report.png" startIcon={<DownloadOutlinedIcon />} variant="contained" disabled={!imageUrl} sx={{ ...insightsPrimaryButtonSx, px: 2.25 }}>Download PNG</Button>
      </DialogActions>
    </Dialog>
  </>;
}
