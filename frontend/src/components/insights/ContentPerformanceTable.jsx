import {
  IconButton,
  Paper,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import ChevronLeftRoundedIcon from "@mui/icons-material/ChevronLeftRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import MetricAvailability from "./MetricAvailability";
import ContentPerformanceRow from "./ContentPerformanceRow";

const INSTAGRAM_HEADERS = ["Content", "Date", "Reach", "Engagement", "Likes / Reactions", "Comments", "Shares"];
const FACEBOOK_HEADERS = ["Content", "Date", "Reach", "Views", "Reactions", "Comments", "Clicks"];

function EmptyRows({ children, loading }) {
  return (
    <TableBody>
      {loading ? [0, 1, 2, 3].map((key) => (
        <TableRow key={key}>
          <TableCell colSpan={7}><Skeleton height={36} /></TableCell>
        </TableRow>
      )) : (
        <TableRow>
          <TableCell colSpan={7} sx={{ height: 150, textAlign: "center" }}>{children}</TableCell>
        </TableRow>
      )}
    </TableBody>
  );
}

export default function ContentPerformanceTable({
  content,
  account,
  loading,
  selected,
  pageNumber,
  pagination,
  onNext,
  onPrevious,
}) {
  const results = content?.results || [];
  const hasNext = Boolean(pagination?.has_next);
  const hasPrevious = Boolean(pagination?.has_previous);
  const tableStatus = content?.availability;
  const isFacebook = String(account?.platform).toLowerCase() === "facebook";
  const headers = isFacebook ? FACEBOOK_HEADERS : INSTAGRAM_HEADERS;

  return (
    <Paper elevation={0} sx={{ border: 0, borderRadius: 0, overflow: "hidden", bgcolor: "#fff" }}>
      <TableContainer sx={{ overflowX: "auto" }}>
        <Table size="small" sx={{ minWidth: 1060, tableLayout: "fixed", width: "100%", "& th, & td": { verticalAlign: "middle" } }}>
          <colgroup>
            <col style={{ width: "33%" }} />
            <col style={{ width: "13%" }} />
            <col style={{ width: "11%" }} />
            <col style={{ width: "12%" }} />
            <col style={{ width: "14%" }} />
            <col style={{ width: "9%" }} />
            <col style={{ width: "8%" }} />
          </colgroup>
          <TableHead>
            <TableRow sx={{ bgcolor: "#F8FAFC" }}>
              {headers.map((header, index) => (
                <TableCell key={header} align={index === 0 ? "left" : "center"} sx={{ py: 1.5, px: index === 0 ? 2 : 1.5, color: "#8795A9", borderBottom: "1px solid #E8EDF4", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.55, textTransform: "uppercase", whiteSpace: "nowrap", bgcolor: "#fff" }}>
                  {header}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          {loading || !results.length ? (
            <EmptyRows loading={loading}>
              {!selected ? (
                <MetricAvailability emptyText="Select an account to view content performance" />
              ) : tableStatus === "available" ? (
                <Typography sx={{ color: "#6F83A3", fontSize: 13 }}>No native content was available in this published snapshot.</Typography>
              ) : (
                <MetricAvailability status={tableStatus} reason={content?.reason} emptyText="Content is unavailable" />
              )}
            </EmptyRows>
          ) : (
            <TableBody>
              {results.map((item) => (
                <ContentPerformanceRow key={item.provider_media_id} item={item} account={account} />
              ))}
            </TableBody>
          )}
        </Table>
      </TableContainer>
      <Paper elevation={0} square sx={{ px: 1.5, py: 0.6, display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 1, borderTop: "1px solid #EDF1F7" }}>
        <Typography sx={{ mr: 0.5, color: "#7D8CA1", fontSize: 11.5 }}>
          {selected && !loading
            ? `Page ${pageNumber}${pagination?.total_pages ? ` of ${pagination.total_pages}` : ""} · Showing ${results.length} of ${pagination?.total_items ?? results.length} items`
            : "Select an account"}
        </Typography>
        <IconButton
          aria-label="Previous content page"
          size="small"
          disabled={!hasPrevious || loading}
          onClick={onPrevious}
          sx={{ border: "1px solid #DBE4F0", borderRadius: "7px", width: 29, height: 29 }}
        ><ChevronLeftRoundedIcon fontSize="small" /></IconButton>
        <IconButton
          aria-label="Next content page"
          size="small"
          disabled={!hasNext || loading}
          onClick={onNext}
          sx={{ border: "1px solid #DBE4F0", borderRadius: "7px", width: 29, height: 29 }}
        ><ChevronRightRoundedIcon fontSize="small" /></IconButton>
      </Paper>
    </Paper>
  );
}
