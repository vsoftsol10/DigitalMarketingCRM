import { useEffect, useMemo, useRef, useState } from "react";
import { renderToStaticMarkup } from "react-dom/server";
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
import reportStyles from "./report.styles.css?inline";
import reportsService from "../../services/reports.service";

function getErrorMessage(error) {
  const data = error?.response?.data;
  if (data instanceof Blob) return "The report could not be generated. Please try again.";
  return data?.message || data?.detail || data?.errors?.date_range || data?.errors?.render
    || error?.message || "The report could not be generated. Please try again.";
}

function buildDocumentHtml(report) {
  const markup = renderToStaticMarkup(<ReportDocument report={report} />);
  return `<!doctype html><html><head><meta charset="utf-8"><style>${reportStyles}</style></head><body style="margin:0;background:#fff">${markup}</body></html>`;
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
      const response = await reportsService.preview({
        organization_id: organization.id,
        social_account_id: account.id,
        platform: scope.platform,
        since: scope.since,
        until: scope.until,
        mode,
        meta_ads: mode === "add_ads" ? adsRows.map((row) => ({ date: row.date, total_leads: row.total_leads })) : [],
      });
      const png = await reportsService.renderPng({
        renderToken: response.render_token,
        html: buildDocumentHtml(response.report),
      });
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
          width: "calc(100% - 64px)",
          maxWidth: 540,
          maxHeight: "min(90vh, 900px)",
          border: "1px solid #e4eaf2",
          borderRadius: 0,
          boxShadow: "0 22px 64px rgba(25, 48, 82, 0.2)",
          overflow: "hidden",
        },
      }}
    >
      <DialogTitle sx={{ px: { xs: 2, sm: 3 }, py: 2.5, pr: 7, color: "#18385f", background: "linear-gradient(110deg, #fff9e9 0%, #fffdf8 100%)", borderBottom: "1px solid #edf0f4" }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <Box sx={{ width: 38, height: 38, flex: "0 0 auto", borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "#fff1c9", color: "#17395f" }}>
            <DownloadOutlinedIcon sx={{ fontSize: 23 }} />
          </Box>
          <Box sx={{ minWidth: 0, pt: 0.1 }}>
            <Typography component="div" sx={{ color: "#18385f", fontSize: { xs: 18, sm: 20 }, fontWeight: 750, lineHeight: 1.3 }}>
              {mode === "add_ads" ? "Add Data & Export" : "Export Current Data"}
            </Typography>
            <Typography sx={{ mt: 0.75, color: "#6b809a", fontSize: 14, lineHeight: 1.55, fontWeight: 400 }}>
              Export currently available CRM data for {organizationLabel}, {accountLabel} ({platformLabel}), and {durationLabel}.
            </Typography>
          </Box>
        </Stack>
        <IconButton aria-label="Close export dialog" onClick={() => { setAdsRows([]); onClose(); }} disabled={generating} sx={{ position: "absolute", right: 12, top: 12, color: "#5b6f89" }}><CloseIcon /></IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ px: { xs: 2, sm: 3 }, py: 2.25, borderColor: "#edf0f4", bgcolor: "#fff", overflowY: "auto", overflowX: "hidden" }}>
        <Stack spacing={2}>
          <Box sx={{ minHeight: 132, px: 2, py: 1.75, border: "1px solid #dce5ef", borderRadius: 2, bgcolor: "#fcfdff", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center" }}>
            <Box sx={{ width: 48, height: 48, mb: 0.75, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "#fff0c2", color: "#ed6b27" }}>
              <CheckRoundedIcon sx={{ fontSize: 32 }} />
            </Box>
            <Typography sx={{ color: "#244366", fontSize: 14, lineHeight: 1.5, fontWeight: 700 }}>
              {exportComplete ? "Completed" : "Exporting..."}
            </Typography>
            <Typography sx={{ mt: 0.25, color: "#8093aa", fontSize: 12.5, lineHeight: 1.5 }}>
              {exportComplete ? "Your report is ready to generate." : "Your file will be downloaded shortly."}
            </Typography>
          </Box>

          <Box>
            <Stack direction="row" spacing={1.25} alignItems="center" sx={{ mb: 0.75 }}>
              <Box sx={{ width: 22, height: 22, flex: "0 0 auto", borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "#244768", color: "#fff" }}>
                <InfoOutlinedIcon sx={{ fontSize: 14 }} />
              </Box>
              <Typography sx={{ color: "#244366", fontSize: 14, fontWeight: 700 }}>This report includes</Typography>
            </Stack>
            <Box component="ul" sx={{ m: 0, pl: 5.5, color: "#72879f", fontSize: 13, lineHeight: 1.75 }}>
              {includedItems.map((item) => <Box component="li" key={item} sx={{ pl: 0.25 }}>{item}</Box>)}
            </Box>
          </Box>

          {error && <Alert severity="error">{error}</Alert>}

          {mode === "add_ads" && <Box sx={{ pt: 1.5, borderTop: "1px solid #e6ebf1" }}>
            <Typography variant="subtitle2" fontWeight={700} mb={1} sx={{ color: "#19385f" }}>Meta Ads (optional, up to 5 rows)</Typography>
            <Box sx={{ width: "100%", overflowX: "hidden", border: "1px solid #dce5ef", bgcolor: "#fff" }}>
              <Table
                size="small"
                sx={{
                  width: "100%",
                  tableLayout: "fixed",
                  borderCollapse: "separate",
                  borderSpacing: 0,
                  m: 0,
                  "& .MuiTableCell-root": { px: { xs: 0.5, sm: 1 }, borderBottom: "1px solid #e3eaf2", borderRight: "1px solid #edf1f6" },
                  "& .MuiTableCell-root:last-child": { borderRight: 0 },
                  "& .MuiTableHead .MuiTableCell-root": { py: 0.9, color: "#435b78", bgcolor: "#f7f9fc", fontSize: 12, lineHeight: 1.4, fontWeight: 700 },
                  "& .MuiTableBody .MuiTableCell-root": { py: 0.65, verticalAlign: "middle", bgcolor: "#fff" },
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
                        "& .MuiOutlinedInput-root": { height: 34, borderRadius: 0, bgcolor: "transparent", px: 0.25, boxShadow: "none", "& fieldset": { border: 0 }, "&.Mui-focused": { boxShadow: "inset 0 -1px #2f6feb" }, "&.Mui-error": { boxShadow: "inset 0 -1px #d32f2f" } },
                        "& .MuiInputBase-input": { minWidth: 0, px: 0.75, fontSize: 12, color: "#344b68" },
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
                        "& .MuiOutlinedInput-root": { height: 34, borderRadius: 0, bgcolor: "transparent", px: 0.25, boxShadow: "none", "& fieldset": { border: 0 }, "&.Mui-focused": { boxShadow: "inset 0 -1px #2f6feb" }, "&.Mui-error": { boxShadow: "inset 0 -1px #d32f2f" } },
                        "& .MuiInputBase-input": { minWidth: 0, px: 0.75, fontSize: 12, color: "#344b68" },
                        "& .MuiFormHelperText-root": { minHeight: 18, mx: 0, mt: 0.5, lineHeight: "18px", whiteSpace: "nowrap", fontSize: 10.5 },
                      }}
                    />
                  </TableCell>
                  <TableCell align="center" sx={{ px: 0.25 }}>
                    <IconButton aria-label={`Remove Meta Ads row ${index + 1}`} onClick={() => setAdsRows((rows) => rows.filter((_, rowIndex) => rowIndex !== index))} sx={{ mt: 0.25, color: "#71839a" }}><DeleteOutlinedIcon /></IconButton>
                  </TableCell>
                </TableRow>)}</TableBody>
              </Table>
            </Box>
            {adsRows.length < 5 && <Button startIcon={<AddCircleOutlinedIcon />} onClick={() => setAdsRows((rows) => [...rows, { date: "", total_leads: "" }])} sx={{ mt: 0.5, textTransform: "none" }}>Add More Data</Button>}
          </Box>}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: 1.75, borderTop: "1px solid #edf0f4", bgcolor: "#fbfcfe", gap: 1 }}>
        <Button onClick={() => { setAdsRows([]); onClose(); }} disabled={generating} sx={{ textTransform: "none", color: "#526780", borderRadius: 2, px: 2 }}>Cancel</Button>
        <Button variant="contained" onClick={generateReport} disabled={!exportComplete || !adsValid} sx={{ borderRadius: 2, px: 2.25, py: 1, boxShadow: "none", textTransform: "none", fontWeight: 650 }}>
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
          width: "calc(100vw - 64px)",
          height: "calc(100dvh - 64px)",
          maxWidth: "min(1536px, calc(100vw - 64px))",
          maxHeight: "calc(100dvh - 64px)",
          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        Report Preview
        <IconButton aria-label="Close report preview" onClick={() => setViewerOpen(false)}><CloseIcon /></IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ flex: "1 1 auto", minHeight: 0, display: "flex", overflow: "hidden", p: { xs: 1, sm: 2 } }}><Box sx={{ width: "100%", height: "100%", minHeight: 0, overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "#f5f7fa" }}>
        {imageUrl && <img src={imageUrl} alt="Generated Insights report" style={{ display: "block", width: "auto", height: "auto", maxWidth: "100%", maxHeight: "100%", objectFit: "contain", margin: "0 auto", boxShadow: "0 3px 16px #182b4a22" }} />}
      </Box></DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button component="a" href={imageUrl || undefined} download="insights-report.png" startIcon={<DownloadOutlinedIcon />} variant="contained" disabled={!imageUrl} sx={{ textTransform: "none" }}>Download PNG</Button>
      </DialogActions>
    </Dialog>
  </>;
}
