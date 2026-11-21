import { Box, Card, CardContent, Skeleton, Typography } from "@mui/material";

export default function DashboardStatCard({
  icon,
  value,
  label,
  tone = "violet",
  loading = false,
  supporting = null,
  variant = "default",
}) {
  const Icon = icon;
  const palettes = {
    violet: { surface: "linear-gradient(145deg, #F0E9FF 0%, #E1E2FF 100%)", accent: "#7650DF", iconSurface: "#EAE3FF", halo: "rgba(126, 101, 226, .2)" },
    rose: { surface: "linear-gradient(145deg, #FFEFF3 0%, #FFDDE7 100%)", accent: "#DF466A", iconSurface: "#FFE2E9", halo: "rgba(221, 82, 119, .2)" },
    mint: { surface: "linear-gradient(145deg, #DFF9F0 0%, #CFF2E6 100%)", accent: "#079C7D", iconSurface: "#D7F6EC", halo: "rgba(24, 167, 135, .2)" },
    sky: { surface: "linear-gradient(145deg, #E9F6FF 0%, #D7EBFF 100%)", accent: "#2585CF", iconSurface: "#DCEFFF", halo: "rgba(61, 143, 207, .2)" },
  };
  const palette = palettes[tone] || palettes.violet;
  const dashboardVariant = variant === "dashboard";

  return (
    <Card
      elevation={0}
      sx={{
        position: "relative",
        overflow: "hidden",
        border: dashboardVariant ? "1px solid #E1E5F0" : "1px solid rgba(255,255,255,.88)",
        borderRadius: "22px",
        minHeight: dashboardVariant ? 160 : 188,
        height: "100%",
        background: dashboardVariant ? "#FFFFFF" : palette.surface,
        boxShadow: dashboardVariant ? "0 4px 12px rgba(41,55,103,.045)" : "0 15px 28px rgba(77,98,154,.16), 0 3px 8px rgba(80,99,151,.1), inset 0 2px 0 rgba(255,255,255,.95), inset 0 -2px 5px rgba(113,128,181,.09)",
        "&::before": {
          ...(dashboardVariant ? { display: "none" } : {}),
          content: "\"\"",
          position: "absolute",
          inset: 4,
          borderRadius: "18px",
          border: "1px solid rgba(255,255,255,.72)",
          pointerEvents: "none",
          zIndex: 1,
        },
        "&::after": {
          ...(dashboardVariant ? { display: "none" } : {}),
          content: "\"\"",
          position: "absolute",
          width: 116,
          height: 116,
          top: -46,
          right: -34,
          borderRadius: "50%",
          bgcolor: palette.halo,
          pointerEvents: "none",
          zIndex: 0,
        },
      }}
    >
      <CardContent
        sx={{
          position: "relative",
          zIndex: 2,
          p: { xs: 2.25, md: 2.5 },

          "&:last-child": {
            pb: 2.5,
          },
        }}
      >
        <Box sx={{ display: dashboardVariant ? "flex" : "block", alignItems: dashboardVariant ? "center" : undefined, mb: dashboardVariant ? 3.5 : 0 }}>
        {/* Icon */}
        <Box
          sx={{
          width: dashboardVariant ? 34 : 62,
          height: dashboardVariant ? 34 : 62,
          borderRadius: dashboardVariant ? "10px" : "50%",
          bgcolor: dashboardVariant ? "transparent" : palette.iconSurface,
          border: dashboardVariant ? "none" : "2px solid rgba(255,255,255,.84)",
          boxShadow: dashboardVariant ? "none" : `0 8px 15px ${palette.halo}, 0 2px 5px rgba(77,98,154,.1), inset 0 2px 3px rgba(255,255,255,.82), inset 0 -2px 3px ${palette.halo}`,

            display: "flex",
            justifyContent: "center",
            alignItems: "center",

            mb: dashboardVariant ? 0 : 2.1,
          }}
        >
          <Icon
            sx={{
              color: dashboardVariant ? "#71809A" : palette.accent,
              fontSize: dashboardVariant ? 21 : 27,
              filter: dashboardVariant ? "none" : "drop-shadow(0 1px 1px rgba(39,54,94,.14))",
            }}
          />
        </Box>
        {dashboardVariant && <Typography sx={{ ml: 1, minWidth: 0, flex: 1, fontSize: 14, fontWeight: 500, color: "#64748B", lineHeight: 1.35 }}>{label}</Typography>}
        </Box>

        {/* Value */}

        <Typography
          sx={{
            fontSize: dashboardVariant ? 34 : 32,
            fontWeight: 700,
            color: "#0F172A",
            lineHeight: 1,
          }}
        >
          {loading ? <Skeleton width={96} height={34} sx={{ bgcolor: "rgba(81,100,150,0.12)" }} /> : value}
        </Typography>

        {/* Label */}

        {!dashboardVariant && <Typography
          sx={{
            mt: 0.8,
            fontSize: 14,

            fontWeight: 500,

            color: "#64748B",
          }}
        >
          {label}
        </Typography>}

        {supporting && <Box sx={{ mt: 0.5 }}>{supporting}</Box>}
      </CardContent>
    </Card>
  );
}
