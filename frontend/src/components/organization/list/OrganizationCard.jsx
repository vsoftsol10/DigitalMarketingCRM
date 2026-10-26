import {
  Avatar,
  Box,
  Card,
  Chip,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import LocationOnOutlinedIcon from "@mui/icons-material/LocationOnOutlined";
import LanguageOutlinedIcon from "@mui/icons-material/LanguageOutlined";
import FiberManualRecordRoundedIcon from "@mui/icons-material/FiberManualRecordRounded";

import { TYPOGRAPHY } from "../../../theme/typography";
import overviewGlassCardSx from "../overview/overviewGlassCardSx";

export default function OrganizationCard({ organization, onClick }) {
  const {
    name,
    industry,
    description,
    location,
    website,
    organization_status,
    subscription_plan,
    // subscription_status,
    social_accounts,
    logo_color,
  } = organization;

  // ==========================================================
  // HELPERS
  // ==========================================================

  const formatIndustry = (value) => {
    if (!value) return "-";

    return value
      .split("_")
      .map((word) => {
        if (word.toLowerCase() === "and") {
          return "&";
        }

        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      })
      .join(" ");
  };

  const formatPlan = (value) => {
    if (!value) return "-";

    return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
  };

  const formatStatus = (value) => {
    if (!value) return "-";

    return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
  };

  const connectedAccountCount = Array.isArray(social_accounts)
    ? social_accounts.filter((account) => account.connected).length
    : 0;

  const initials =
    name
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((item) => item[0])
      .join("")
      .toUpperCase() || "--";

  // ==========================================================
  // STATUS COLORS
  // ==========================================================

  const organizationStatusStyles = {
    ACTIVE: {
      bgcolor: "#ECFDF3",
      color: "#16A34A",
      borderColor: "#A7F3D0",
    },

    INACTIVE: {
      bgcolor: "#F8FAFC",
      color: "#64748B",
      borderColor: "#CBD5E1",
    },

    SUSPENDED: {
      bgcolor: "#FEF2F2",
      color: "#DC2626",
      borderColor: "#FECACA",
    },
  };

  const statusStyle =
    organizationStatusStyles[organization_status] ||
    organizationStatusStyles.INACTIVE;

  // ==========================================================
  // CARD
  // ==========================================================

  return (
    <Card
      elevation={0}
      onClick={onClick}
      sx={{
        ...overviewGlassCardSx,
        height: "100%",
        p: 3,
        cursor: "pointer",
        transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",

        "&:hover": {
          borderColor: "rgba(255,255,255,1)",
          boxShadow: "0 13px 27px rgba(69,96,145,.17), 0 3px 8px rgba(74,99,145,.07), inset 0 0 0 1px rgba(171,194,229,.25), inset 0 2px 0 rgba(255,255,255,1), inset 0 -2px 4px rgba(113,136,179,.07)",
          transform: "translateY(-2px)",
        },
      }}
    >
      {/* ====================================================
          HEADER
      ==================================================== */}

      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 2,
          mb: 3,
        }}
      >
        <Stack
          direction="row"
          spacing={2}
          sx={{
            minWidth: 0,
          }}
        >
          <Avatar
            sx={{
              width: 54,
              height: 54,
              flexShrink: 0,
              bgcolor: logo_color || "#2563EB",
              background: `linear-gradient(145deg, ${logo_color || "#2563EB"}, rgba(122, 99, 228, .94))`,
              fontWeight: 700,
              fontSize: 22,
              border: "2px solid rgba(255,255,255,.9)",
              boxShadow: "0 5px 12px rgba(73, 100, 148, .18), inset 0 1px 0 rgba(255,255,255,.5)",
            }}
          >
            {initials}
          </Avatar>

          <Box
            sx={{
              minWidth: 0,
            }}
          >
            <Typography
              sx={{
                ...TYPOGRAPHY.cardTitle,
                overflowWrap: "anywhere",
              }}
            >
              {name || "-"}
            </Typography>

            <Typography
              sx={{
                ...TYPOGRAPHY.small,
                mt: 0.3,
              }}
            >
              {formatIndustry(industry)}
            </Typography>
          </Box>
        </Stack>

        <Chip
          icon={
            <FiberManualRecordRoundedIcon
              sx={{
                fontSize: "9px !important",
                color: `${statusStyle.color} !important`,
              }}
            />
          }
          label={formatStatus(organization_status)}
          size="small"
          sx={{
            flexShrink: 0,
            bgcolor: statusStyle.bgcolor,
            color: statusStyle.color,
            border: "1px solid",
            borderColor: statusStyle.borderColor,
            fontWeight: 600,
            borderRadius: "999px",
          }}
        />
      </Box>

      {/* ====================================================
          DESCRIPTION
      ==================================================== */}

      <Typography
        sx={{
          ...TYPOGRAPHY.bodySmall,
          color: "#475569",

          display: "-webkit-box",
          overflow: "hidden",
          WebkitBoxOrient: "vertical",
          WebkitLineClamp: 2,

          minHeight: 44,
          mb: 2.5,
        }}
      >
        {description || "-"}
      </Typography>

      {/* ====================================================
          LOCATION
      ==================================================== */}

      <Stack
        direction="row"
        spacing={0.75}
        alignItems="center"
        sx={{
          minWidth: 0,
          mb: 2.5,
          color: "#64748B",
        }}
      >
        <LocationOnOutlinedIcon
          sx={{
            fontSize: 17,
            flexShrink: 0,
            color: "#5684CB",
            filter: "drop-shadow(0 1px 2px rgba(86,132,203,.18))",
          }}
        />

        <Typography
          sx={{
            ...TYPOGRAPHY.caption,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {location || "Location not added"}
        </Typography>
      </Stack>

      {/* ====================================================
          WEBSITE
      ==================================================== */}

      {website && (
        <Stack
          direction="row"
          spacing={0.75}
          alignItems="center"
          sx={{
            minWidth: 0,
            mb: 2.5,
            color: "#64748B",
          }}
        >
          <LanguageOutlinedIcon
            sx={{
              fontSize: 17,
              flexShrink: 0,
              color: "#3D9BBA",
              filter: "drop-shadow(0 1px 2px rgba(61,155,186,.18))",
            }}
          />

          <Typography
            component="span"
            sx={{
              ...TYPOGRAPHY.caption,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              color: "#2563EB",
            }}
          >
            {website.replace(/^https?:\/\//, "")}
          </Typography>
        </Stack>
      )}

      {/* ====================================================
          CONNECTED SOCIAL ACCOUNTS
      ==================================================== */}

      <Stack
        direction="row"
        spacing={0.75}
        alignItems="center"
        sx={{
          color: "#64748B",
        }}
      >
        <GroupsOutlinedIcon
          sx={{
            fontSize: 17,
            color: "#765FD0",
          }}
        />

        <Typography sx={TYPOGRAPHY.caption}>
          {connectedAccountCount}{" "}
          {connectedAccountCount === 1 ? "account" : "accounts"} connected
        </Typography>
      </Stack>

      <Divider
        sx={{
          my: 2.5,
        }}
      />

      {/* ====================================================
          FOOTER
      ==================================================== */}

      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-start",
          alignItems: "center",
        }}
      >
        <Chip
          label={formatPlan(subscription_plan)}
          size="small"
          sx={{
            bgcolor: "#EEF4FF",
            color: "#2563EB",
            fontWeight: 600,
            borderRadius: "999px",
            border: "1px solid #BFDBFE",
          }}
        />
      </Box>
    </Card>
  );
}
