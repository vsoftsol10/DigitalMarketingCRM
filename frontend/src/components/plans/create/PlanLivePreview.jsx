import { Box, Chip, Paper, Stack, Typography } from "@mui/material";

import CheckIcon from "@mui/icons-material/Check";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";

import { useFormContext } from "react-hook-form";

function formatPrice(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

export default function PlanLivePreview() {
  const { watch } = useFormContext();

  const values = watch();

  const price =
    values.billing_cycle === "yearly"
      ? values.yearly_price
      : values.monthly_price;

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

  const features = Array.isArray(values.features)
    ? values.features.filter(Boolean)
    : [];

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
          mb: 2,
          pl: 0.25,
        }}
      >
        <AutoAwesomeOutlinedIcon
          sx={{
            fontSize: 17,
            color: "#94A3B8",
          }}
        />

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

          p: "26px 26px 22px",

          borderRadius: "20px",

          border: "1px solid #D7E3F4",

          backgroundColor: "#FFFFFF",

          boxShadow: "0 2px 8px rgba(15, 23, 42, 0.03)",
        }}
      >
        {/* ====================================
            PLAN TYPE
        ==================================== */}

        <Typography
          sx={{
            fontSize: "14px",
            fontWeight: 500,
            lineHeight: "20px",

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
            mt: 0.5,

            fontSize: "30px",
            fontWeight: 700,
            lineHeight: "38px",

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

            minHeight: 44,

            fontSize: "16px",
            fontWeight: 400,
            lineHeight: "24px",

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
            PRICE
        ==================================== */}

        {/* <Box
          sx={{
            width: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "baseline",
            // mt: 2,
            mb: 3,
          }}
        >
          <Typography
            component="span"
            sx={{
              fontSize: "30px",
              fontWeight: 700,
              lineHeight: "38px",
              letterSpacing: "-0.025em",
              color: "#2563EB",
            }}
          >
            ₹{formatPrice(price)}
          </Typography>

          <Typography
            component="span"
            sx={{
              ml: 0.4,
              fontSize: "16px",
              fontWeight: 400,
              lineHeight: "24px",
              color: "#94A3B8",
            }}
          >
            /{values.billing_cycle === "yearly" ? "year" : "month"}
          </Typography>
        </Box> */}
        <Box
          sx={{
            mt: 2.5,
            mb: 3,

            display: "flex",
            justifyContent: "center",
            gap: 3,
          }}
        >
          <Box>
            <Typography
              sx={{
                fontSize: "24px",
                fontWeight: 700,
                color: "#2563EB",
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
                fontSize: "24px",
                fontWeight: 700,
                color: "#2563EB",
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

            mb: 2.25,
          }}
        />

        {/* ====================================
            LIMITS
        ==================================== */}

        <Stack
          spacing={1.05}
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

                  color: "#10B981",

                  flexShrink: 0,
                }}
              />

              <Typography
                sx={{
                  fontSize: "16px",
                  fontWeight: 400,
                  lineHeight: "24px",

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

            mt: 2.25,
            mb: 1.75,
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
            height: 32,

            alignSelf: "flex-start",

            borderRadius: "16px",

            backgroundColor:
              values.status === "inactive" ? "#F1F5F9" : "#ECFDF5",

            border: "1px solid",

            borderColor: values.status === "inactive" ? "#CBD5E1" : "#86EFAC",

            color: values.status === "inactive" ? "#64748B" : "#059669",

            fontSize: "14px",
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
      </Paper>
    </Box>
  );
}
