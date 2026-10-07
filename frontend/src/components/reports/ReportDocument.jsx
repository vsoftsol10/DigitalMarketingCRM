import "./report.styles.css";
import companyLogo from "./vsoft-logo.png?inline";

function formatNumber(value, maximumFractionDigits = 1) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits }).format(number);
}

function metricValue(stat) {
  if (stat?.metric?.availability !== "available") return "—";
  return formatNumber(stat.metric.value, stat.label === "Total Posts" ? 0 : 1);
}

function shortDate(value) {
  if (!value) return "—";
  const parsed = new Date(`${value.slice(0, 10)}T00:00:00`);
  return Number.isNaN(parsed.getTime())
    ? "—"
    : new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short" }).format(parsed);
}

function chartDate(value, includeMonth = false) {
  if (!value) return "";
  const parsed = new Date(`${value.slice(0, 10)}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return "";
  return new Intl.DateTimeFormat("en-GB", includeMonth
    ? { day: "2-digit", month: "short" }
    : { day: "2-digit" }).format(parsed);
}

function captionText(row) {
  const caption = String(row.caption || "")
    .replace(/https?:\/\/\S+/gi, " ")
    .replace(/\b(?:read more(?: at)?|learn more|visit|click here)\s*$/i, "")
    .replace(/\s+/g, " ")
    .trim();
  if (caption) return caption;
  return row.media_type === "VIDEO" ? "Video post" : "Image post";
}

function buildObservation(report, peakPoint, contentCount) {
  const peakSummary = peakPoint
    ? `Daily reach peaked at ${formatNumber(peakPoint.value, 0)} on ${shortDate(peakPoint.date)}.`
    : "Daily reach data was unavailable for this reporting period.";

  if (report.mode === "add_ads" && report.meta_ads?.length) {
    const leads = report.meta_ads.reduce((total, row) => {
      const value = Number(row.total_leads);
      return total + (Number.isFinite(value) ? value : 0);
    }, 0);
    return `${peakSummary} The entered Meta Ads rows recorded ${formatNumber(leads, 0)} total leads.`;
  }

  const highestPostReach = report.content_performance?.[0]?.metrics?.reach;
  if (highestPostReach?.availability === "available") {
    return `${peakSummary} The highest-reach post recorded ${formatNumber(highestPostReach.value, 0)} reach.`;
  }
  return `${peakSummary} The report includes ${formatNumber(contentCount, 0)} posts from the selected snapshot.`;
}

export default function ReportDocument({ report }) {
  const points = report.daily_reach || [];
  const availablePoints = points.filter((point) => point.value !== null && Number.isFinite(Number(point.value)));
  const maxReach = Math.max(...availablePoints.map((point) => Number(point.value)), 1);
  const peakPoint = availablePoints.reduce((highest, point) => (
    !highest || Number(point.value) > Number(highest.value) ? point : highest
  ), null);
  const peakIndex = peakPoint ? points.findIndex((point) => point.date === peakPoint.date) : -1;
  const content = report.content_performance || [];
  const postCountStat = report.stats?.find((stat) => stat.label === "Total Posts");
  const contentCount = postCountStat?.metric?.value ?? content.length;
  const labelInterval = Math.max(1, Math.ceil(points.length / 8));
  const valueInterval = Math.max(1, Math.ceil(points.length / 7));
  const observation = buildObservation(report, peakPoint, contentCount);
  const reportTitle = report.mode === "add_ads" ? "SOCIAL MEDIA & META ADS REPORT" : "SOCIAL MEDIA REPORT";
  const showAds = report.mode === "add_ads" && report.meta_ads?.length > 0;

  return (
    <article id="report-document" className="report-document">
      <header className="report-header">
        <img className="report-brand-logo" src={companyLogo} alt="The Vsoft" />
        <div className={`report-header-meta${report.mode === "add_ads" ? " add-ads" : ""}`}>
          <strong>{reportTitle}</strong>
          <span>{shortDate(report.date_range.since)} – {shortDate(report.date_range.until)}</span>
        </div>
      </header>

      <section className="report-account">
        <h1>{report.organization.name}</h1>
        <p>
          <span className={`report-platform-icon ${report.account.platform}`} aria-hidden="true">
            {report.account.platform === "instagram" ? "◎" : "f"}
          </span>
          {report.account.platform === "instagram" ? "Instagram" : "Facebook"} · {report.account.name}
        </p>
      </section>

      <main className="report-main">
        <section className="report-performance">
          <h2>Social Media Performance</h2>
          <div className="report-stat-grid">
            {(report.stats || []).map((stat) => (
              <div className="report-stat" key={stat.label}>
                <span>{stat.label}</span>
                <strong>{metricValue(stat)}</strong>
              </div>
            ))}
          </div>

          {showAds && (
            <section className="report-ads">
              <h2>Meta Ads</h2>
              <table>
                <thead><tr><th>Date</th><th>Total Leads</th></tr></thead>
                <tbody>
                  {report.meta_ads.map((row, index) => (
                    <tr key={`${row.date}-${index}`}>
                      <td>{shortDate(row.date)}</td>
                      <td>{formatNumber(row.total_leads, 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </section>

        <section className="report-chart-section">
          <div className="report-section-heading">
            <h2>Daily Reach</h2>
            {peakPoint && <span className="report-peak">Highest reach · {shortDate(peakPoint.date)} · {formatNumber(peakPoint.value, 0)}</span>}
          </div>
          <div className="report-chart" role="img" aria-label="Daily reach chart">
            <div className="report-chart-yaxis" aria-hidden="true">
              {[1, 0.75, 0.5, 0.25, 0].map((fraction) => (
                <span key={fraction}>{formatNumber(maxReach * fraction, 0)}</span>
              ))}
            </div>
            <div className="report-chart-plot" style={{ gridTemplateColumns: `repeat(${Math.max(points.length, 1)}, minmax(0, 1fr))` }}>
              {points.map((point, index) => {
                const valid = point.value !== null && Number.isFinite(Number(point.value));
                const barHeight = valid ? Math.max(2, (Number(point.value) / maxReach) * 100) : 0;
                const previousPoint = points[index - 1];
                const monthStarted = previousPoint && point.date.slice(0, 7) !== previousPoint.date.slice(0, 7);
                const showDate = points.length <= 10 || index === 0 || index === points.length - 1
                  || index % labelInterval === 0 || monthStarted;
                const showValue = valid && (points.length <= 8 || index === peakIndex || index % valueInterval === 0);
                return (
                  <div className="report-chart-column" key={point.date}>
                    <div className="report-chart-bar-wrap">
                      {showValue && <span className="report-chart-value" style={{ bottom: `calc(${barHeight}% + 3px)` }}>{formatNumber(point.value, 0)}</span>}
                      <div className={`report-chart-bar${valid ? "" : " unavailable"}`} style={{ height: valid ? `${barHeight}%` : "2px" }} />
                    </div>
                    <span className="report-chart-date">
                      {showDate ? chartDate(point.date, index === 0 || monthStarted || index === points.length - 1) : ""}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
          {!availablePoints.length && <p className="report-empty-note">Reach was not available in the selected content.</p>}
        </section>
      </main>

      <section className="report-content-section">
        <h2>Top 5 Posts by Reach</h2>
        <table>
          <colgroup>
            <col className="report-content-col" />
            <col className="report-date-col" />
            {report.content_fields.map((field) => <col key={field.key} />)}
          </colgroup>
          <thead>
            <tr>
              <th>Content</th>
              <th>Date</th>
              {report.content_fields.map((field) => <th key={field.key}>{field.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {content.length ? content.map((row) => (
              <tr key={row.provider_media_id}>
                <td className="report-content-name">
                  <span className={`report-thumbnail${row.media_type === "VIDEO" ? " video" : " image"}`} aria-label={row.media_type === "VIDEO" ? "Video" : "Image"}>
                    {row.media_type === "VIDEO" ? "▶" : "▧"}
                  </span>
                  <span className="report-caption" title={captionText(row)}>{captionText(row)}</span>
                </td>
                <td>{shortDate(row.published_at?.slice(0, 10))}</td>
                {report.content_fields.map((field) => {
                  const metric = row.metrics?.[field.key];
                  return <td key={field.key}>{metric?.availability === "available" ? formatNumber(metric.value, 0) : "—"}</td>;
                })}
              </tr>
            )) : (
              <tr><td colSpan={2 + report.content_fields.length} className="report-empty">No eligible content in the selected snapshot.</td></tr>
            )}
          </tbody>
        </table>
      </section>

      <footer className="report-observation">
        <div className="report-observation-rule" />
        <div>
          <strong>KEY OBSERVATION</strong>
          <p>{observation}</p>
        </div>
      </footer>
    </article>
  );
}
