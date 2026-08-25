// import { Box, Container, Paper } from "@mui/material";

// export default function AuthLayout({ children }) {
//   return (
//     <Box
//       sx={{
//         minHeight: "100vh",
//         display: "flex",
//         alignItems: "center",
//         justifyContent: "center",
//         bgcolor: "background.default",
//         p: 2,
//       }}
//     >
//       <Container maxWidth="sm">
//         <Paper
//           elevation={3}
//           sx={{
//             p: 5,
//             borderRadius: 3,
//           }}
//         >
//           {children}
//         </Paper>
//       </Container>
//     </Box>
//   );
// }

// -------------------------------

// import {
//   Box,
//   Container,
//   Paper,
//   Stack,
//   Typography,
// } from "@mui/material";

// import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
// import InsightsRoundedIcon from "@mui/icons-material/InsightsRounded";

// const FEATURES = [
//   "Manage all clients from one place",
//   "Schedule social media posts",
//   "Track campaigns & analytics",
//   "Generate reports instantly",
// ];

// export default function AuthLayout({ children }) {
//   return (
//     <Box
//       sx={{
//         minHeight: "100vh",
//         bgcolor: "#F8FAFC",
//         display: "flex",
//         alignItems: "center",
//         py: { xs: 4, md: 6 },
//       }}
//     >
//       <Container maxWidth="xl">
//         <Paper
//           elevation={0}
//           sx={{
//             overflow: "hidden",
//             borderRadius: 6,
//             border: "1px solid #E5E7EB",
//             display: "grid",
//             gridTemplateColumns: {
//               xs: "1fr",
//               lg: "1.1fr 0.9fr",
//             },
//             minHeight: {
//               xs: "auto",
//               lg: "720px",
//             },
//             bgcolor: "#fff",
//             boxShadow: "0 20px 60px rgba(15,23,42,0.08)",
//           }}
//         >
//           {/* LEFT SECTION */}
//           <Box
//             sx={{
//               display: {
//                 xs: "none",
//                 lg: "flex",
//               },
//               flexDirection: "column",
//               justifyContent: "space-between",
//               p: 8,
//               color: "#fff",
//               background:
//                 "linear-gradient(135deg,#2563EB 0%,#1D4ED8 40%,#0F172A 100%)",
//               position: "relative",
//               overflow: "hidden",
//             }}
//           >
//             <Box
//               sx={{
//                 position: "absolute",
//                 width: 300,
//                 height: 300,
//                 borderRadius: "50%",
//                 bgcolor: "rgba(255,255,255,.08)",
//                 top: -80,
//                 right: -80,
//               }}
//             />

//             <Box
//               sx={{
//                 position: "absolute",
//                 width: 220,
//                 height: 220,
//                 borderRadius: "50%",
//                 bgcolor: "rgba(255,255,255,.05)",
//                 bottom: -60,
//                 left: -60,
//               }}
//             />

//             <Box sx={{ position: "relative", zIndex: 2 }}>
//               <Stack direction="row" spacing={2} alignItems="center">
//                 <Box
//                   sx={{
//                     width: 60,
//                     height: 60,
//                     borderRadius: 3,
//                     bgcolor: "rgba(255,255,255,.15)",
//                     display: "grid",
//                     placeItems: "center",
//                     backdropFilter: "blur(10px)",
//                   }}
//                 >
//                   <InsightsRoundedIcon sx={{ fontSize: 34 }} />
//                 </Box>

//                 <Typography
//                   variant="h4"
//                   fontWeight={700}
//                 >
//                   Digital Marketing Platform
//                 </Typography>
//               </Stack>

//               <Typography
//                 sx={{
//                   mt: 5,
//                   fontSize: 18,
//                   lineHeight: 1.8,
//                   color: "rgba(255,255,255,.9)",
//                   maxWidth: 500,
//                 }}
//               >
//                 Manage clients, schedule content, monitor
//                 campaigns and generate reports from one
//                 powerful dashboard.
//               </Typography>

//               <Stack spacing={3} mt={7}>
//                 {FEATURES.map((item) => (
//                   <Stack
//                     key={item}
//                     direction="row"
//                     spacing={2}
//                     alignItems="center"
//                   >
//                     <CheckCircleRoundedIcon />

//                     <Typography fontSize={17}>
//                       {item}
//                     </Typography>
//                   </Stack>
//                 ))}
//               </Stack>
//             </Box>

//             <Typography
//               sx={{
//                 position: "relative",
//                 zIndex: 2,
//                 color: "rgba(255,255,255,.75)",
//               }}
//             >
//               © 2026 Digital Marketing Platform
//             </Typography>
//           </Box>

//           {/* RIGHT SECTION */}
//           <Box
//             sx={{
//               display: "flex",
//               alignItems: "center",
//               justifyContent: "center",
//               px: {
//                 xs: 3,
//                 sm: 6,
//                 md: 8,
//               },
//               py: {
//                 xs: 5,
//                 md: 8,
//               },
//             }}
//           >
//             <Box
//               sx={{
//                 width: "100%",
//                 maxWidth: 430,
//               }}
//             >
//               {children}
//             </Box>
//           </Box>
//         </Paper>
//       </Container>
//     </Box>
//   );
// }


import { useEffect, useRef, useState } from "react";
import { Box, Stack, Typography, GlobalStyles, Chip } from "@mui/material";
import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookIcon from "@mui/icons-material/Facebook";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import InsightsIcon from "@mui/icons-material/Insights";

/**
 * ---------------------------------------------------------------
 * DESIGN TOKENS — shared across Login.jsx / LoginForm.jsx
 * ---------------------------------------------------------------
 */
export const tokens = {
  color: {
    panelBg: "#0F1428",
    formBg: "#F5F6FA",
    primary: "#5B4FE9",
    accent: "#17C3B2",
    textOnDark: "#F4F5F9",
    textOnDarkMuted: "rgba(244,245,249,0.65)",
    textPrimary: "#12131A",
    textMuted: "#6B7280",
  },
  font: {
    display: "'Space Grotesk', 'Inter', sans-serif",
    body: "'Inter', 'Space Grotesk', sans-serif",
  },
};

const METRICS = [
  {
    id: "followers",
    label: "Followers reached",
    icon: InstagramIcon,
    target: 128400,
    format: (n) => `${(n / 1000).toFixed(1)}k`,
    delta: "+12.4%",
  },
  {
    id: "engagement",
    label: "Avg. engagement rate",
    icon: TrendingUpIcon,
    target: 6.8,
    format: (n) => `${n.toFixed(1)}%`,
    delta: "+2.1%",
  },
  {
    id: "reports",
    label: "Client reports exported",
    icon: InsightsIcon,
    target: 342,
    format: (n) => `${Math.round(n)}`,
    delta: "+58 this month",
  },
];

function useCountUp(target, durationMs = 1100) {
  const [value, setValue] = useState(0);
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion) {
      setValue(target);
      return;
    }

    let raf;
    const start = performance.now();

    const tick = (now) => {
      const progress = Math.min((now - start) / durationMs, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(target * eased);
      if (progress < 1) raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);

  return value;
}

function InsightCard({ metric, delayMs }) {
  const value = useCountUp(metric.target);
  const Icon = metric.icon;

  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={2}
      sx={{
        p: 2,
        borderRadius: 3,
        bgcolor: "rgba(255,255,255,0.035)",
        border: "1px solid rgba(255,255,255,0.08)",
        animation: "fadeInUp 0.55s ease-out both",
        animationDelay: `${delayMs}ms`,
      }}
    >
      <Box
        sx={{
          width: 38,
          height: 38,
          borderRadius: 2,
          display: "grid",
          placeItems: "center",
          bgcolor: "rgba(91,79,233,0.18)",
          color: tokens.color.accent,
          flexShrink: 0,
        }}
      >
        <Icon fontSize="small" />
      </Box>

      <Box sx={{ minWidth: 0 }}>
        <Typography
          sx={{
            fontFamily: tokens.font.display,
            fontWeight: 700,
            fontSize: "1.3rem",
            lineHeight: 1.2,
            color: tokens.color.textOnDark,
          }}
        >
          {metric.format(value)}
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.25 }}>
          <Typography
            variant="caption"
            sx={{ color: tokens.color.textOnDarkMuted }}
            noWrap
          >
            {metric.label}
          </Typography>
          <Chip
            label={metric.delta}
            size="small"
            sx={{
              height: 18,
              fontSize: "0.65rem",
              fontWeight: 600,
              color: tokens.color.accent,
              bgcolor: "rgba(23,195,178,0.14)",
              "& .MuiChip-label": { px: 0.75 },
            }}
          />
        </Stack>
      </Box>
    </Stack>
  );
}

export default function AuthLayout({ children }) {
  return (
    <>
      <GlobalStyles
        styles={{
          "@keyframes fadeInUp": {
            from: { opacity: 0, transform: "translateY(12px)" },
            to: { opacity: 1, transform: "translateY(0)" },
          },
          "@media (prefers-reduced-motion: reduce)": {
            "*": {
              animationDuration: "0.01ms !important",
              animationIterationCount: "1 !important",
            },
          },
        }}
      />

      <Box
        sx={{
          minHeight: "100dvh",
          display: "flex",
          flexDirection: { xs: "column", md: "row" },
          bgcolor: tokens.color.formBg,
        }}
      >
        {/* Compact brand bar — mobile & tablet only */}
        <Stack
          direction="row"
          alignItems="center"
          spacing={1.5}
          sx={{
            display: { xs: "flex", md: "none" },
            px: 3,
            py: 2.25,
            bgcolor: tokens.color.panelBg,
          }}
        >
          <Box
            sx={{
              width: 30,
              height: 30,
              borderRadius: 1.5,
              bgcolor: tokens.color.primary,
              display: "grid",
              placeItems: "center",
            }}
          >
            <InsightsIcon sx={{ fontSize: 16, color: "#fff" }} />
          </Box>
          <Typography
            sx={{
              fontFamily: tokens.font.display,
              fontWeight: 700,
              color: tokens.color.textOnDark,
              fontSize: "1rem",
            }}
          >
            Reach&nbsp;Suite
          </Typography>
        </Stack>

        {/* Brand / insights panel — desktop only */}
        <Box
          sx={{
            display: { xs: "none", md: "flex" },
            flexDirection: "column",
            justifyContent: "space-between",
            width: { md: "45%", lg: "42%" },
            px: { md: 5, lg: 7 },
            py: 6,
            bgcolor: tokens.color.panelBg,
            backgroundImage:
              "radial-gradient(circle at 12% 8%, rgba(91,79,233,0.30), transparent 55%), radial-gradient(circle at 88% 92%, rgba(23,195,178,0.14), transparent 50%)",
            position: "relative",
          }}
        >
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <Box
              sx={{
                width: 34,
                height: 34,
                borderRadius: 1.5,
                bgcolor: tokens.color.primary,
                display: "grid",
                placeItems: "center",
              }}
            >
              <InsightsIcon sx={{ fontSize: 18, color: "#fff" }} />
            </Box>
            <Typography
              sx={{
                fontFamily: tokens.font.display,
                fontWeight: 700,
                color: tokens.color.textOnDark,
                fontSize: "1.15rem",
              }}
            >
              Reach&nbsp;Suite
            </Typography>
          </Stack>

          <Box sx={{ my: { md: 4, lg: 5 } }}>
            <Typography
              sx={{
                fontFamily: tokens.font.display,
                fontWeight: 700,
                color: tokens.color.textOnDark,
                fontSize: { md: "1.8rem", lg: "2.15rem" },
                lineHeight: 1.18,
                letterSpacing: "-0.01em",
                mb: 1.5,
              }}
            >
              Every client's socials,
              <br /> one dashboard.
            </Typography>
            <Typography
              sx={{
                color: tokens.color.textOnDarkMuted,
                fontFamily: tokens.font.body,
                fontSize: "0.9rem",
                maxWidth: 340,
              }}
            >
              Manage accounts, track engagement, and export
              client-ready reports without leaving Reach Suite.
            </Typography>

            <Stack direction="row" spacing={1} sx={{ mt: 3 }}>
              {[InstagramIcon, FacebookIcon, LinkedInIcon].map((Icon, i) => (
                <Box
                  key={i}
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    bgcolor: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    display: "grid",
                    placeItems: "center",
                    color: tokens.color.textOnDarkMuted,
                  }}
                >
                  <Icon sx={{ fontSize: 16 }} />
                </Box>
              ))}
            </Stack>
          </Box>

          <Stack spacing={1.5}>
            {METRICS.map((metric, i) => (
              <InsightCard key={metric.id} metric={metric} delayMs={i * 120} />
            ))}
          </Stack>
        </Box>

        {/* Form panel */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            px: { xs: 2.5, sm: 5 },
            py: { xs: 4, md: 4 },
          }}
        >
          <Box sx={{ width: "100%" }}>{children}</Box>
        </Box>
      </Box>
    </>
  );
}