import {
  ChatBubbleOutlineOutlined,
  EditOutlined,
  ImageOutlined,
  Instagram,
  MoreHoriz,
  PauseOutlined,
  PlayArrowOutlined,
  SendOutlined,
  VideoCameraBackOutlined,
  LayersOutlined,
} from "@mui/icons-material";

import {
  Box,
  Button,
  Chip,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import { TYPOGRAPHY } from "../../theme/typography";

const CONTENT_CONFIG = {
  Story: {
    icon: ImageOutlined,
    background: "linear-gradient(135deg, #FCE7F3 0%, #FDF2F8 100%)",
    color: "#EC4899",
  },
  Reel: {
    icon: VideoCameraBackOutlined,
    background: "linear-gradient(135deg, #CBD5E1 0%, #E2E8F0 100%)",
    color: "#64748B",
  },
  Post: {
    icon: ImageOutlined,
    background: "linear-gradient(135deg, #DBEAFE 0%, #EFF6FF 100%)",
    color: "#3B82F6",
  },
  Carousel: {
    icon: LayersOutlined,
    background: "linear-gradient(135deg, #EDE9FE 0%, #F5F3FF 100%)",
    color: "#7C3AED",
  },
};

function TriggerIcon({ triggerType }) {
  if (triggerType === "Keyword") {
    return (
      <Box component="span" sx={{ fontWeight: 700 }}>
        #
      </Box>
    );
  }

  if (triggerType === "Comment") {
    return <ChatBubbleOutlineOutlined sx={{ fontSize: 14 }} />;
  }

  return <SendOutlined sx={{ fontSize: 14 }} />;
}

function StatusDot({ isActive }) {
  return (
    <Box
      sx={{
        width: 6,
        height: 6,
        borderRadius: "50%",
        backgroundColor: isActive ? "#10B981" : "#94A3B8",
        flexShrink: 0,
      }}
    />
  );
}

export default function DMAutomationCard({
  automation,
  onEdit,
  onToggleStatus,
}) {
  const contentConfig =
    CONTENT_CONFIG[automation.contentType] || CONTENT_CONFIG.Post;

  const ContentIcon = contentConfig.icon;

  const isActive = automation.status === "active";

  return (
    <Box
      sx={{
        width: "100%",
        overflow: "hidden",
        borderRadius: "18px",
        border: "1px solid #E2E8F0",
        backgroundColor: "#FFFFFF",
      }}
    >
      {/* Content Preview */}
      <Box
        sx={{
          position: "relative",
          height: 136,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: contentConfig.background,
        }}
      >
        {/* Content Type */}
        <Chip
          icon={
            <Instagram
              sx={{
                fontSize: "14px !important",
                color: "#EC4899 !important",
              }}
            />
          }
          label={automation.contentType}
          size="small"
          sx={{
            position: "absolute",
            top: 14,
            left: 14,
            height: 28,
            backgroundColor: "#FFFFFF",
            border: "1px solid #E2E8F0",
            "& .MuiChip-label": {
              ...TYPOGRAPHY.caption,
              color: "#475569",
              px: 1,
            },
          }}
        />

        {/* Status */}
        <Chip
          icon={<StatusDot isActive={isActive} />}
          label={isActive ? "Active" : "Disabled"}
          size="small"
          sx={{
            position: "absolute",
            top: 14,
            right: 14,
            height: 28,
            backgroundColor: isActive ? "#ECFDF5" : "#F1F5F9",
            border: `1px solid ${isActive ? "#A7F3D0" : "#CBD5E1"}`,
            "& .MuiChip-icon": {
              ml: 1.25,
              mr: -4 / 8,
            },
            "& .MuiChip-label": {
              ...TYPOGRAPHY.caption,
              color: isActive ? "#059669" : "#64748B",
              px: 1.25,
            },
          }}
        />

        <ContentIcon
          sx={{
            fontSize: 42,
            color: contentConfig.color,
            opacity: 0.55,
          }}
        />
      </Box>

      {/* Card Body */}
      <Box sx={{ p: 2.25 }}>
        <Stack direction="row" spacing={1.25} alignItems="center">
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "#2563EB",
              color: "#FFFFFF",
              flexShrink: 0,
            }}
          >
            <Typography
              sx={{
                fontSize: "13px",
                fontWeight: 700,
                lineHeight: 1,
                color: "#FFFFFF",
              }}
            >
              {automation.organization
                .split(" ")
                .map((word) => word[0])
                .join("")
                .slice(0, 2)
                .toUpperCase()}
            </Typography>
          </Box>

          <Box sx={{ minWidth: 0 }}>
            <Typography
              sx={{
                ...TYPOGRAPHY.cardTitle,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {automation.name}
            </Typography>

            <Typography sx={TYPOGRAPHY.bodySmall}>
              {automation.organization}
            </Typography>
          </Box>

          <Box sx={{ ml: "auto !important" }}>
            <IconButton
              size="small"
              aria-label="More automation options"
              sx={{
                color: "#64748B",
              }}
            >
              <MoreHoriz fontSize="small" />
            </IconButton>
          </Box>
        </Stack>

        {/* Content */}
        <Box
          sx={{
            mt: 2,
            px: 1.5,
            py: 1,
            borderRadius: "10px",
            backgroundColor: "#F8FAFC",
          }}
        >
          <Stack direction="row" spacing={1}>
            <Typography sx={TYPOGRAPHY.bodySmall}>Content:</Typography>

            <Typography
              sx={{
                ...TYPOGRAPHY.bodySmall,
                color: "#475569",
                fontWeight: 500,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {automation.contentTitle}
            </Typography>
          </Stack>
        </Box>

        {/* Trigger */}
        <Box sx={{ mt: 1.5 }}>
          <Chip
            icon={<TriggerIcon triggerType={automation.triggerType} />}
            label={
              automation.triggerType === "Keyword" && automation.triggerValue
                ? `Keyword: "${automation.triggerValue}"`
                : automation.triggerType
            }
            size="small"
            sx={{
              height: 30,
              backgroundColor: "#EFF6FF",
              color: "#2563EB",
              borderRadius: "8px",
              "& .MuiChip-icon": {
                color: "#2563EB",
                ml: 0.75,
              },
              "& .MuiChip-label": {
                ...TYPOGRAPHY.caption,
                color: "#2563EB",
                px: 1,
              },
            }}
          />
        </Box>

        {/* Reply */}
        <Box
          sx={{
            mt: 1.5,
            p: 1.5,
            borderRadius: "14px",
            backgroundColor: "#F8FAFC",
            border: "1px solid #E2E8F0",
          }}
        >
          <Stack direction="row" spacing={0.75} alignItems="center">
            <ChatBubbleOutlineOutlined
              sx={{
                fontSize: 13,
                color: "#94A3B8",
              }}
            />

            <Typography
              sx={{
                ...TYPOGRAPHY.caption,
                color: "#94A3B8",
                textTransform: "uppercase",
              }}
            >
              Auto Reply
            </Typography>
          </Stack>

          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,
              mt: 0.75,
              color: "#64748B",
              fontStyle: "italic",
              lineHeight: "21px",
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            "{automation.replyMessage}"
          </Typography>
        </Box>

        {/* Actions */}
        <Stack
          direction="row"
          spacing={1}
          sx={{
            mt: 1.75,
          }}
        >
          <Button
            size="small"
            startIcon={<EditOutlined />}
            onClick={() => onEdit?.(automation)}
            sx={{
              ...TYPOGRAPHY.button,
              color: "#475569",
              borderColor: "#CBD5E1",
              border: "1px solid #CBD5E1",
              borderRadius: "10px",
              px: 1.5,
            }}
          >
            Edit
          </Button>

          <Button
            size="small"
            startIcon={isActive ? <PauseOutlined /> : <PlayArrowOutlined />}
            onClick={() => onToggleStatus?.(automation)}
            sx={{
              ...TYPOGRAPHY.button,
              color: isActive ? "#DC2626" : "#16A34A",
              borderColor: isActive ? "#FECACA" : "#BBF7D0",
              border: "1px solid",
              borderRadius: "10px",
              px: 1.5,
            }}
          >
            {isActive ? "Disable" : "Enable"}
          </Button>
        </Stack>
      </Box>
    </Box>
  );
}