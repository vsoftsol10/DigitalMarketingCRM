import { SvgIcon } from "@mui/material";

// MUI's icon pack doesn't ship the current X mark or TikTok, so
// these fill the gap using the same SvgIcon wrapper — they accept
// the same sx/fontSize props as any @mui/icons-material icon.

export function XIcon(props) {
  return (
    <SvgIcon {...props} viewBox="0 0 24 24">
      <path d="M18.244 2H21.5l-7.5 8.57L23 22h-7.19l-5.63-6.78L3.5 22H0l8.03-9.17L1 2h7.35l5.09 6.19L18.244 2Zm-1.26 18h2.03L7.1 4H4.9l12.084 16Z" />
    </SvgIcon>
  );
}

export function TikTokIcon(props) {
  return (
    <SvgIcon {...props} viewBox="0 0 24 24">
      <path d="M16.6 5.82c-.9-.98-1.4-2.25-1.4-3.57h-3.03v13.7c0 1.53-1.24 2.77-2.77 2.77a2.77 2.77 0 1 1 .3-5.53c.18 0 .36.01.53.04V9.98a5.9 5.9 0 0 0-.83-.06 5.8 5.8 0 1 0 5.8 5.8V8.63a8.5 8.5 0 0 0 4.9 1.56V7.16a5.4 5.4 0 0 1-3.5-1.34Z" />
    </SvgIcon>
  );
}