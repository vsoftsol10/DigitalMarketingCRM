import { Avatar, Box, Link, TableCell, TableRow, Typography } from "@mui/material";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import dayjs from "dayjs";
import MetricAvailability from "./MetricAvailability";
import formatCompactNumber from "../../utils/formatters/formatCompactNumber";

function FieldValue({ metric }) {
  if (metric?.availability !== "available" || metric.value == null) {
    return <MetricAvailability status={metric?.availability || "unavailable"} reason={metric?.reason} compact />;
  }
  return <Typography sx={{ color: "#4D668C", fontSize: 12.5, whiteSpace: "nowrap" }}>
    {typeof metric.value === "number" ? formatCompactNumber(metric.value) : String(metric.value)}
  </Typography>;
}

function ContentTitle({ item }) {
  const title = item.caption
    ? item.caption
    : "Native social content";

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, minWidth: 0 }}>
      <Avatar variant="rounded" sx={{ width: 44, height: 44, flexShrink: 0, bgcolor: "#F1F3FA", color: "#6B6AE7", border: "1px solid #E7ECF4" }}>
        <ImageOutlinedIcon sx={{ fontSize: 20 }} />
      </Avatar>
      <Box sx={{ minWidth: 0 }}>
        {item.permalink ? (
          <Link href={item.permalink} target="_blank" rel="noreferrer" underline="hover" color="inherit">
            <Typography noWrap title={title} sx={{ maxWidth: "100%", fontSize: 13, fontWeight: 600 }}>{title}</Typography>
          </Link>
        ) : (
          <Typography noWrap title={title} sx={{ maxWidth: "100%", fontSize: 13, fontWeight: 600, color: "#263B5D" }}>{title}</Typography>
        )}
      </Box>
    </Box>
  );
}

export default function ContentPerformanceRow({ item, account }) {
  const isFacebook = String(account?.platform).toLowerCase() === "facebook";
  const performanceMetric = isFacebook ? item.metrics?.views : item.metrics?.engagement;
  const socialReactions = isFacebook ? item.metrics?.reactions : item.metrics?.likes;
  const finalMetric = isFacebook ? item.metrics?.clicks : item.metrics?.shares;
  return (
    <TableRow hover sx={{ "& td": { borderBottom: "1px solid #EEF2F6", py: 1.25 }, "&:last-child td": { borderBottom: 0 } }}>
      <TableCell align="left" sx={{ pl: 2 }}><ContentTitle item={item} /></TableCell>
      <TableCell align="center" sx={{ whiteSpace: "nowrap", color: "#56677F", fontSize: 12 }}>{item.published_at ? dayjs(item.published_at).format("MMM D, YYYY") : "Date unavailable"}</TableCell>
      <TableCell align="center"><FieldValue metric={item.metrics?.reach} /></TableCell>
      <TableCell align="center"><FieldValue metric={performanceMetric} /></TableCell>
      <TableCell align="center"><FieldValue metric={socialReactions} /></TableCell>
      <TableCell align="center"><FieldValue metric={item.metrics?.comments} /></TableCell>
      <TableCell align="center" sx={{ pr: 2 }}><FieldValue metric={finalMetric} /></TableCell>
    </TableRow>
  );
}
