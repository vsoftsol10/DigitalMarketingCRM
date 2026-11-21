import { Box, Chip, Paper, Stack, Typography } from "@mui/material";

import CheckIcon from "@mui/icons-material/Check";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import { planTone } from "../plansGlassSx";

import { useFormContext } from "react-hook-form";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

export default function PlanLivePreview() {
  const { watch } = useFormContext();

  const values = watch();

  const tone = planTone();

  /*
   * ==========================================
   * LIMITS
   * ==========================================
   */

  const limits = [
    `${values.limits?.accounts ?? 0} Social Accounts`,
    `${values.limits?.posts ?? 0} Posts / Posters per month`,
    `${values.limits?.videos ?? 0} Videos per month`,
    `${values.limits?.ads ?? 0} Ads / Campaigns`,
    `${values.limits?.dm_automations ?? 0} DM Automations`,
  ];

  /*
   * ==========================================
   * FEATURES
   * ==========================================
   */

  const features = String(values.highlights || "")
    .split(/\n/)
    .map((feature) => feature.trim())
    .filter(Boolean);

  return (
    <Box
      sx={{
        position: {
          xs: "static",
          lg: "sticky",
        },

        top: 24,

        width: "100%",
        minWidth: 0,
      }}
    >
      {/* ======================================
          LIVE PREVIEW LABEL
      ====================================== */}

      <Stack
        direction="row"
        alignItems="center"
        spacing={0.6}
        sx={{
          mb: 1.25,
          pl: 0.25,
        }}
      >
        <AutoAwesomeOutlinedIcon sx={{ fontSize: 17, color: tone.icon }} />

        <Typography
          sx={{
            fontSize: "14px",
            fontWeight: 600,
            lineHeight: "20px",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: "#94A3B8",
          }}
        >
          Live Preview
        </Typography>
      </Stack>

      {/* ======================================
          PREVIEW CARD
      ====================================== */}

      <Paper
        elevation={0}
        sx={{
          width: "100%",
          boxSizing: "border-box",

          p: { xs: 2, sm: 2.25 },

          borderRadius: "18px",

          border: `1px solid ${tone.border}`,

          background: tone.surface,
          boxShadow: "0 8px 20px rgba(54,76,132,0.07)",
        }}
      >
        {/* ====================================
            PLAN TYPE
        ==================================== */}

        <Typography
          sx={{
            fontSize: "12px",
            fontWeight: 600,
            lineHeight: "18px",

            color: "#94A3B8",

            textTransform: "uppercase",

            textAlign: "center",
          }}
        >
          {(values.type || "Basic").toUpperCase()}
        </Typography>

        {/* ====================================
            PLAN NAME
        ==================================== */}

        <Typography
          sx={{
            mt: 0.35,

            fontSize: "24px",
            fontWeight: 700,
            lineHeight: "30px",

            letterSpacing: "-0.025em",

            color: "#1E293B",

            textAlign: "center",

            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {values.name || "Plan Name"}
        </Typography>

        {/* ====================================
            DESCRIPTION
        ==================================== */}

        <Typography
          sx={{
            mt: 0.4,

            minHeight: 42,

            fontSize: "14px",
            fontWeight: 400,
            lineHeight: "21px",

            color: "#64748B",

            textAlign: "center",

            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {values.description || "Plan description"}
        </Typography>

        {/* ====================================
            PRICING
        ==================================== */}
        <Box
          sx={{
            mt: 1.5,
            mb: 1.5,

            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 1.5,
            p: 1.25,
            borderRadius: "12px",
            border: "1px solid #E6EAF4",
            background: tone.tint,
            "& > :nth-of-type(2)": { borderLeft: "1px solid #E0E5F0", pl: 1.5 },
          }}
        >
          <Box>
            <Typography
              sx={{
                fontSize: "20px",
                fontWeight: 700,
                lineHeight: "26px",
                color: tone.accent,
                textAlign: "center",
              }}
            >
              ₹{formatPrice(values.monthly_price)}
            </Typography>

            <Typography
              sx={{
                fontSize: "13px",
                color: "#94A3B8",
                textAlign: "center",
              }}
            >
              / month
            </Typography>
          </Box>

          <Box>
            <Typography
              sx={{
                fontSize: "20px",
                fontWeight: 700,
                lineHeight: "26px",
                color: tone.accent,
                textAlign: "center",
              }}
            >
              ₹{formatPrice(values.yearly_price)}
            </Typography>

            <Typography
              sx={{
                fontSize: "13px",
                color: "#94A3B8",
                textAlign: "center",
              }}
            >
              / year
            </Typography>
          </Box>
        </Box>

        {/* ====================================
            DIVIDER
        ==================================== */}

        <Box
          sx={{
            width: "100%",
            height: "1px",

            backgroundColor: "#E2E8F0",

            mb: 1.5,
          }}
        />

        {/* ====================================
            LIMITS
        ==================================== */}

        <Stack
          spacing={0.75}
          sx={{
            width: "100%",
          }}
        >
          {limits.map((item, index) => (
            <Stack
              key={`limit-${index}`}
              direction="row"
              alignItems="center"
              spacing={1}
            >
              <CheckIcon
                sx={{
                  fontSize: 17,

                  color: tone.accent,

                  flexShrink: 0,
                }}
              />

              <Typography
                sx={{
                  fontSize: "14px",
                  fontWeight: 400,
                  lineHeight: "21px",

                  color: "#475569",
                }}
              >
                {item}
              </Typography>
            </Stack>
          ))}
        </Stack>

        {/* ====================================
            STATUS DIVIDER
        ==================================== */}

        <Box
          sx={{
            width: "100%",
            height: "1px",

            backgroundColor: "#E2E8F0",

            mt: 1.5,
            mb: 1.25,
          }}
        />

        {/* ====================================
            STATUS
        ==================================== */}

        <Chip
          label={values.status === "inactive" ? "Inactive" : "Active"}
          size="small"
          icon={
            <Box
              component="span"
              sx={{
                width: 8,
                height: 8,

                borderRadius: "50%",

                backgroundColor:
                  values.status === "inactive" ? "#94A3B8" : "#10B981",

                ml: "4px",
              }}
            />
          }
          sx={{
            height: 28,

            alignSelf: "flex-start",

            borderRadius: "16px",

            backgroundColor:
              values.status === "inactive" ? "#F1F5F9" : "#ECFDF5",

            border: "1px solid",

            borderColor: values.status === "inactive" ? "#CBD5E1" : "#86EFAC",

            color: values.status === "inactive" ? "#64748B" : "#059669",

            fontSize: "13px",
            fontWeight: 500,

            "& .MuiChip-icon": {
              marginLeft: "7px",
              marginRight: "2px",
            },

            "& .MuiChip-label": {
              px: 1,
            },
          }}
        />
        {features.length > 0 && (
          <Box
            sx={{
              mt: 1.5,
              pt: 1.25,
              borderTop: "1px solid rgba(145,166,202,0.24)",
            }}
          >
            <Typography
              sx={{
                mb: 1,
                color: "#7183A1",
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
              }}
            >
              Plan Highlights
            </Typography>
            <Stack spacing={0.65}>
              {features.map((feature, index) => (
                <Stack
                  key={`highlight-${index}`}
                  direction="row"
                  alignItems="flex-start"
                  spacing={0.8}
                >
                  <CheckIcon sx={{ mt: 0.2, color: tone.accent, fontSize: 16, flexShrink: 0 }} />
                  <Typography
                    sx={{ color: "#526783", fontSize: 13.5, lineHeight: 1.5 }}
                  >
                    {feature}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Box>
        )}
      </Paper>
    </Box>
  );
}
