import {
  ChatBubbleOutlineOutlined,
  Close,
  Instagram,
} from "@mui/icons-material";

import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from "@mui/material";

import { useEffect, useState } from "react";

import { TYPOGRAPHY } from "../../theme/typography";

import {
  MOCK_INSTAGRAM_ACCOUNTS,
  MOCK_INSTAGRAM_CONTENT,
} from "../../data/dmAutomationData";

const STEPS = [
  "Name",
  "Account",
  "Content",
  "Trigger",
  "Reply",
  "Status",
  "Review",
];

const INITIAL_FORM = {
  name: "",
  organizationId: "",
  contentId: "",
  contentType: "",
  triggerType: "",
  triggerValue: "",
  replyMessage: "",
  status: "active",
};

function isStepValid(step, form) {
  switch (step) {
    case 0:
      return Boolean(form.name.trim());

    case 1:
      return Boolean(form.organizationId);

    case 2:
      return Boolean(form.contentId);

    case 3:
      if (!form.triggerType) {
        return false;
      }

      if (form.triggerType === "Keyword" && !form.triggerValue.trim()) {
        return false;
      }

      return true;

    case 4:
      return Boolean(form.replyMessage.trim());

    case 5:
      return Boolean(form.status);

    case 6:
      return true;

    default:
      return false;
  }
}

export default function CreateAutomationDialog({
  open,
  onClose,
  onSubmit,
  submitting = false,
  initialData = null,
}) {
  const [activeStep, setActiveStep] = useState(0);

  const [form, setForm] = useState(INITIAL_FORM);

  const isEditMode = Boolean(initialData);

  useEffect(() => {
    if (!open) {
      return;
    }

    if (initialData) {
      setForm({
        name: initialData.name || "",
        organizationId: initialData.organizationId || "",
        contentId: initialData.contentId || "",
        contentType: initialData.contentType || "",
        triggerType: initialData.triggerType || "",
        triggerValue: initialData.triggerValue || "",
        replyMessage: initialData.replyMessage || "",
        status: initialData.status || "active",
      });

      setActiveStep(0);
      return;
    }

    setForm(INITIAL_FORM);
    setActiveStep(0);
  }, [open, initialData]);

  const handleClose = () => {
    setForm(INITIAL_FORM);
    setActiveStep(0);
    onClose?.();
  };

  const handleChange = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleContinue = async () => {
    if (activeStep < STEPS.length - 1) {
      setActiveStep((current) => current + 1);
      return;
    }

    await onSubmit?.(form);
  };

  const handleBack = () => {
    setActiveStep((current) => Math.max(current - 1, 0));
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="md"
      PaperProps={{
        sx: {
          width: "100%",
          maxWidth: 720,

          borderRadius: "18px",

          overflow: "hidden",

          boxShadow: "0 20px 50px rgba(15, 23, 42, 0.18)",
        },
      }}
    >
      {/* =====================================================
          HEADER
      ====================================================== */}

      <DialogTitle
        sx={{
          px: 2.5,
          py: 2,

          minHeight: 64,

          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",

          borderBottom: "1px solid #E2E8F0",
        }}
      >
        <Typography sx={TYPOGRAPHY.cardTitle}>Create Automation</Typography>

        <IconButton
          size="small"
          onClick={handleClose}
          aria-label="Close create automation dialog"
          sx={{
            color: "#94A3B8",
          }}
        >
          <Close fontSize="small" />
        </IconButton>
      </DialogTitle>

      {/* =====================================================
          CONTENT
      ====================================================== */}

      <DialogContent
        sx={{
          px: 2.5,
          py: 2.5,
        }}
      >
        {/* Stepper */}

        <Stepper
          activeStep={activeStep}
          sx={{
            mb: 3,

            "& .MuiStep-root": {
              px: 0.5,
            },

            "& .MuiStepLabel-label": {
              ...TYPOGRAPHY.caption,
            },

            "& .MuiStepLabel-label.Mui-active": {
              color: "#2563EB",
              fontWeight: 600,
            },

            "& .MuiStepLabel-label.Mui-completed": {
              color: "#059669",
              fontWeight: 600,
            },

            "& .MuiStepIcon-root": {
              fontSize: 24,
            },

            "& .MuiStepIcon-root.Mui-active": {
              color: "#2563EB",
            },

            "& .MuiStepIcon-root.Mui-completed": {
              color: "#10B981",
            },
          }}
        >
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Current Step */}

        <Box
          sx={{
            minHeight: 250,
          }}
        >
          {activeStep === 0 && (
            <NameStep
              value={form.name}
              onChange={(value) => handleChange("name", value)}
            />
          )}

          {activeStep === 1 && (
            <AccountStep
              value={form.organizationId}
              onChange={(value) => handleChange("organizationId", value)}
            />
          )}

          {activeStep === 2 && (
            <ContentStep
              organizationId={form.organizationId}
              value={form.contentId}
              onChange={(content) => {
                handleChange("contentId", content.id);
                handleChange("contentType", content.type);
              }}
            />
          )}

          {activeStep === 3 && (
            <TriggerStep
              triggerType={form.triggerType}
              triggerValue={form.triggerValue}
              onChange={(field, value) => handleChange(field, value)}
            />
          )}

          {activeStep === 4 && (
            <ReplyStep
              value={form.replyMessage}
              onChange={(value) => handleChange("replyMessage", value)}
            />
          )}

          {activeStep === 5 && (
            <StatusStep
              value={form.status}
              onChange={(value) => handleChange("status", value)}
            />
          )}

          {activeStep === 6 && <ReviewStep form={form} />}
        </Box>
      </DialogContent>

      {/* =====================================================
          FOOTER
      ====================================================== */}

      <Box
        sx={{
          px: 2.5,
          py: 1.75,

          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",

          borderTop: "1px solid #E2E8F0",
        }}
      >
        <Button
          onClick={handleClose}
          sx={{
            ...TYPOGRAPHY.button,
            color: "#475569",
          }}
        >
          Cancel
        </Button>

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          {activeStep > 0 && (
            <Button
              variant="outlined"
              onClick={handleBack}
              sx={{
                ...TYPOGRAPHY.button,

                minWidth: 82,
                height: 40,

                borderRadius: "10px",

                color: "#475569",
                borderColor: "#CBD5E1",
              }}
            >
              Back
            </Button>
          )}

          <Button
            variant="contained"
            onClick={handleContinue}
            disabled={submitting || !isStepValid(activeStep, form)}
          >
            {submitting
              ? isEditMode
                ? "Updating..."
                : "Creating..."
              : activeStep === STEPS.length - 1
                ? isEditMode
                  ? "Update Automation"
                  : "Create Automation"
                : "Continue"}
          </Button>
        </Box>
      </Box>
    </Dialog>
  );
}

/* ============================================================
   STEP 1 — NAME
============================================================ */

function NameStep({ value, onChange }) {
  return (
    <Box>
      {/* Instagram Information */}
      <Box
        sx={{
          mb: 3,

          display: "flex",
          alignItems: "center",

          gap: 1.5,

          px: 2,
          py: 1.75,

          borderRadius: "14px",

          backgroundColor: "#FFF8FB",

          border: "1px solid #F4DDE8",
        }}
      >
        <Box
          sx={{
            width: 38,
            height: 38,

            flexShrink: 0,

            display: "flex",
            alignItems: "center",
            justifyContent: "center",

            borderRadius: "11px",

            backgroundColor: "#FFF1F7",
          }}
        >
          <Instagram
            sx={{
              fontSize: 20,
              color: "#EC4899",
            }}
          />
        </Box>

        <Box>
          <Typography
            sx={{
              ...TYPOGRAPHY.inputLabel,
              color: "#1E293B",
            }}
          >
            Instagram
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,
              mt: 0.15,
            }}
          >
            This automation will respond to interactions on your Instagram
            content.
          </Typography>
        </Box>
      </Box>

      {/* Section Heading */}
      <Typography sx={TYPOGRAPHY.sectionTitle}>Automation Name</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        Give your automation a recognizable name.
      </Typography>

      {/* Form Field */}
      <Box sx={{ mt: 2.5 }}>
        <Typography sx={TYPOGRAPHY.inputLabel}>Automation Name *</Typography>

        <Box
          component="input"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="e.g. Summer Offer"
          sx={{
            display: "block",

            width: "100%",
            height: 46,

            mt: 0.75,

            px: 1.5,

            boxSizing: "border-box",

            border: "1px solid #CBD5E1",
            borderRadius: "10px",

            outline: "none",

            fontFamily: "inherit",

            ...TYPOGRAPHY.body,

            backgroundColor: "#FFFFFF",

            "&:focus": {
              borderColor: "#2563EB",

              boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.10)",
            },

            "&::placeholder": {
              color: "#94A3B8",
            },
          }}
        />

        <Typography
          sx={{
            ...TYPOGRAPHY.helperText,
            mt: 0.75,
          }}
        >
          Give your automation a recognizable name.
        </Typography>
      </Box>
    </Box>
  );
}

function AccountStep({ value, onChange }) {
  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>
        Select Instagram Account
      </Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        Select the organization whose Instagram content will be automated.
      </Typography>

      <Box sx={{ mt: 2.5 }}>
        <Typography sx={TYPOGRAPHY.inputLabel}>Instagram Account *</Typography>

        <Box
          component="select"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          sx={{
            display: "block",

            width: "100%",
            height: 46,

            mt: 0.75,

            px: 1.5,

            boxSizing: "border-box",

            border: "1px solid #CBD5E1",
            borderRadius: "10px",

            outline: "none",

            fontFamily: "inherit",

            ...TYPOGRAPHY.body,

            color: value ? "#475569" : "#94A3B8",

            backgroundColor: "#FFFFFF",

            cursor: "pointer",

            "&:focus": {
              borderColor: "#2563EB",

              boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.10)",
            },
          }}
        >
          <option value="" disabled>
            Select organization
          </option>

          {MOCK_INSTAGRAM_ACCOUNTS.map((account) => (
            <option key={account.id} value={account.id}>
              {account.organization} — {account.username}
            </option>
          ))}
        </Box>

        <Typography
          sx={{
            ...TYPOGRAPHY.helperText,
            mt: 0.75,
          }}
        >
          Choose the Instagram account whose content this automation will
          monitor.
        </Typography>
      </Box>

      {/* Selected Account Preview */}
      {value && <SelectedAccountPreview accountId={value} />}
    </Box>
  );
}

function SelectedAccountPreview({ accountId }) {
  const account = MOCK_INSTAGRAM_ACCOUNTS.find((item) => item.id === accountId);

  if (!account) {
    return null;
  }

  return (
    <Box
      sx={{
        mt: 2,

        p: 1.75,

        display: "flex",
        alignItems: "center",

        gap: 1.5,

        borderRadius: "14px",

        border: "1px solid #DBEAFE",

        backgroundColor: "#F8FBFF",
      }}
    >
      <Box
        sx={{
          width: 40,
          height: 40,

          flexShrink: 0,

          display: "flex",
          alignItems: "center",
          justifyContent: "center",

          borderRadius: "50%",

          backgroundColor: "#2563EB",
        }}
      >
        <Typography
          sx={{
            ...TYPOGRAPHY.caption,

            fontWeight: 700,

            color: "#FFFFFF",
          }}
        >
          {account.organization
            .split(" ")
            .map((word) => word[0])
            .join("")
            .slice(0, 2)
            .toUpperCase()}
        </Typography>
      </Box>

      <Box sx={{ minWidth: 0 }}>
        <Typography sx={TYPOGRAPHY.cardTitle}>
          {account.organization}
        </Typography>

        <Typography sx={TYPOGRAPHY.bodySmall}>{account.username}</Typography>
      </Box>
    </Box>
  );
}

function ContentStep({ organizationId, value, onChange }) {
  const [search, setSearch] = useState("");

  const contents = MOCK_INSTAGRAM_CONTENT.filter(
    (content) => content.organizationId === organizationId,
  );

  const filteredContents = contents.filter((content) =>
    content.title.toLowerCase().includes(search.toLowerCase()),
  );

  const selectedContent = contents.find((content) => content.id === value);

  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>
        Select Instagram Content
      </Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        Choose the specific Post, Reel, or Carousel this automation will
        monitor.
      </Typography>

      {/* Search */}
      <Box
        component="input"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search content by title or caption..."
        sx={{
          display: "block",
          width: "100%",
          height: 44,
          mt: 2.25,
          px: 1.5,
          boxSizing: "border-box",
          border: "1px solid #CBD5E1",
          borderRadius: "10px",
          outline: "none",
          fontFamily: "inherit",
          ...TYPOGRAPHY.body,
          "&:focus": {
            borderColor: "#2563EB",
            boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.10)",
          },
          "&::placeholder": {
            color: "#94A3B8",
          },
        }}
      />

      {/* Content List */}
      <Stack spacing={1.25} sx={{ mt: 2 }}>
        {filteredContents.map((content) => {
          const selected = content.id === value;

          return (
            <Box
              key={content.id}
              onClick={() => onChange(content)}
              sx={{
                p: 1.5,

                display: "flex",
                alignItems: "center",

                gap: 1.5,

                borderRadius: "12px",

                border: selected ? "1px solid #2563EB" : "1px solid #E2E8F0",

                backgroundColor: selected ? "#EFF6FF" : "#FFFFFF",

                cursor: "pointer",

                transition:
                  "border-color 0.15s ease, background-color 0.15s ease",

                "&:hover": {
                  borderColor: "#93C5FD",
                  backgroundColor: "#F8FBFF",
                },
              }}
            >
              {/* Thumbnail */}
              <Box
                sx={{
                  width: 52,
                  height: 52,

                  flexShrink: 0,

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  borderRadius: "9px",

                  background:
                    content.type === "Carousel"
                      ? "linear-gradient(135deg, #EDE9FE, #F5F3FF)"
                      : content.type === "Reel"
                        ? "linear-gradient(135deg, #FCE7F3, #FDF2F8)"
                        : "linear-gradient(135deg, #DBEAFE, #EFF6FF)",
                }}
              >
                <Typography
                  sx={{
                    ...TYPOGRAPHY.caption,
                    fontWeight: 700,
                  }}
                >
                  {content.type}
                </Typography>
              </Box>

              {/* Content Information */}
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography
                  sx={{
                    ...TYPOGRAPHY.cardTitle,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {content.title}
                </Typography>

                <Typography
                  sx={{
                    ...TYPOGRAPHY.bodySmall,
                    mt: 0.25,
                  }}
                >
                  {content.type} · {content.publishedAt}
                </Typography>
              </Box>

              {/* Selection */}
              <Box
                sx={{
                  width: 20,
                  height: 20,

                  flexShrink: 0,

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  borderRadius: "50%",

                  border: selected ? "6px solid #2563EB" : "2px solid #CBD5E1",

                  backgroundColor: "#FFFFFF",
                }}
              />
            </Box>
          );
        })}
      </Stack>

      {/* Selected Content */}
      {selectedContent && (
        <Box
          sx={{
            mt: 2,

            p: 1.75,

            borderRadius: "14px",

            backgroundColor: "#F8FAFC",

            border: "1px solid #E2E8F0",
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.caption,
              textTransform: "uppercase",
              color: "#94A3B8",
            }}
          >
            Selected Content
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.cardTitle,
              mt: 0.5,
            }}
          >
            {selectedContent.title}
          </Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,
              mt: 0.25,
            }}
          >
            Instagram {selectedContent.type} · Published{" "}
            {selectedContent.publishedAt}
          </Typography>
        </Box>
      )}
    </Box>
  );
}

function TriggerStep({ triggerType, triggerValue, onChange }) {
  const triggerOptions = [
    {
      value: "Keyword",
      title: "Keyword",
      description: "Trigger when a specific keyword is used.",
      symbol: "#",
    },
    {
      value: "Comment",
      title: "Comment",
      description: "Trigger when someone comments on the selected content.",
      symbol: "💬",
    },
    {
      value: "Message",
      title: "Message",
      description:
        "Trigger when someone sends a message related to the content.",
      symbol: "✈",
    },
  ];

  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>Select Trigger</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        Choose what interaction should trigger the automated reply.
      </Typography>

      {/* Trigger Options */}
      <Stack spacing={1.25} sx={{ mt: 2.5 }}>
        {triggerOptions.map((option) => {
          const selected = triggerType === option.value;

          return (
            <Box
              key={option.value}
              onClick={() => onChange("triggerType", option.value)}
              sx={{
                p: 1.75,

                display: "flex",
                alignItems: "center",

                gap: 1.5,

                borderRadius: "14px",

                border: selected ? "1px solid #2563EB" : "1px solid #E2E8F0",

                backgroundColor: selected ? "#EFF6FF" : "#FFFFFF",

                cursor: "pointer",

                "&:hover": {
                  borderColor: "#93C5FD",
                  backgroundColor: "#F8FBFF",
                },
              }}
            >
              {/* Icon */}
              <Box
                sx={{
                  width: 40,
                  height: 40,

                  flexShrink: 0,

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  borderRadius: "11px",

                  backgroundColor: selected ? "#DBEAFE" : "#F8FAFC",

                  color: selected ? "#2563EB" : "#64748B",

                  fontSize: 18,
                  fontWeight: 700,
                }}
              >
                {option.symbol}
              </Box>

              {/* Text */}
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography
                  sx={{
                    ...TYPOGRAPHY.cardTitle,
                    fontSize: "14px",
                  }}
                >
                  {option.title}
                </Typography>

                <Typography
                  sx={{
                    ...TYPOGRAPHY.bodySmall,
                    mt: 0.15,
                  }}
                >
                  {option.description}
                </Typography>
              </Box>

              {/* Radio */}
              <Box
                sx={{
                  width: 20,
                  height: 20,

                  flexShrink: 0,

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  borderRadius: "50%",

                  border: selected ? "6px solid #2563EB" : "2px solid #CBD5E1",

                  backgroundColor: "#FFFFFF",
                }}
              />
            </Box>
          );
        })}
      </Stack>

      {/* Keyword Input */}
      {triggerType === "Keyword" && (
        <Box sx={{ mt: 2 }}>
          <Typography sx={TYPOGRAPHY.inputLabel}>Keyword *</Typography>

          <Box
            component="input"
            value={triggerValue}
            onChange={(event) => onChange("triggerValue", event.target.value)}
            placeholder="e.g. price"
            sx={{
              display: "block",

              width: "100%",
              height: 46,

              mt: 0.75,

              px: 1.5,

              boxSizing: "border-box",

              border: "1px solid #CBD5E1",
              borderRadius: "10px",

              outline: "none",

              fontFamily: "inherit",

              ...TYPOGRAPHY.body,

              "&:focus": {
                borderColor: "#2563EB",

                boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.10)",
              },

              "&::placeholder": {
                color: "#94A3B8",
              },
            }}
          />

          <Typography
            sx={{
              ...TYPOGRAPHY.helperText,
              mt: 0.75,
            }}
          >
            The automation will trigger when this keyword is detected.
          </Typography>
        </Box>
      )}
    </Box>
  );
}

function ReplyStep({ value, onChange }) {
  const MAX_LENGTH = 500;

  const characterCount = value.length;

  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>Automatic Reply</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        Write the message that should be sent when the selected trigger occurs.
      </Typography>

      {/* Reply Message */}
      <Box sx={{ mt: 2.5 }}>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
        >
          <Typography sx={TYPOGRAPHY.inputLabel}>Reply Message *</Typography>

          <Typography
            sx={{
              ...TYPOGRAPHY.caption,
              color: characterCount > MAX_LENGTH ? "#DC2626" : "#94A3B8",
            }}
          >
            {characterCount}/{MAX_LENGTH}
          </Typography>
        </Stack>

        <Box
          component="textarea"
          value={value}
          onChange={(event) => {
            if (event.target.value.length <= MAX_LENGTH) {
              onChange(event.target.value);
            }
          }}
          placeholder="e.g. Hey! Thanks for reaching out. How can we help you?"
          rows={6}
          sx={{
            display: "block",

            width: "100%",

            mt: 0.75,

            px: 1.5,
            py: 1.25,

            boxSizing: "border-box",

            resize: "vertical",

            border: "1px solid #CBD5E1",
            borderRadius: "10px",

            outline: "none",

            fontFamily: "inherit",

            ...TYPOGRAPHY.body,

            backgroundColor: "#FFFFFF",

            "&:focus": {
              borderColor: "#2563EB",

              boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.10)",
            },

            "&::placeholder": {
              color: "#94A3B8",
            },
          }}
        />

        <Typography
          sx={{
            ...TYPOGRAPHY.helperText,
            mt: 0.75,
          }}
        >
          Keep your response short, friendly, and relevant to the selected
          trigger.
        </Typography>
      </Box>

      {/* Preview */}
      <Box
        sx={{
          mt: 2.5,

          p: 1.75,

          borderRadius: "14px",

          backgroundColor: "#F8FAFC",

          border: "1px solid #E2E8F0",
        }}
      >
        <Stack direction="row" alignItems="center" spacing={0.75}>
          <ChatBubbleOutlineOutlined
            sx={{
              fontSize: 15,
              color: "#64748B",
            }}
          />

          <Typography
            sx={{
              ...TYPOGRAPHY.caption,

              color: "#64748B",

              textTransform: "uppercase",
            }}
          >
            Reply Preview
          </Typography>
        </Stack>

        <Box
          sx={{
            mt: 1.25,

            maxWidth: "90%",

            px: 1.5,
            py: 1.25,

            borderRadius: "14px 14px 14px 4px",

            backgroundColor: "#FFFFFF",

            border: "1px solid #E2E8F0",
          }}
        >
          <Typography
            sx={{
              ...TYPOGRAPHY.bodySmall,

              color: value ? "#475569" : "#94A3B8",

              fontStyle: value ? "normal" : "italic",

              whiteSpace: "pre-wrap",

              wordBreak: "break-word",
            }}
          >
            {value || "Your automatic reply will appear here."}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}

function StatusStep({ value, onChange }) {
  const options = [
    {
      value: "active",
      title: "Active",
      description: "Start this automation immediately after it is created.",
    },
    {
      value: "inactive",
      title: "Disabled",
      description:
        "Create the automation but keep it disabled until you enable it.",
    },
  ];

  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>Automation Status</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        Choose whether this automation should be active right away.
      </Typography>

      <Stack spacing={1.25} sx={{ mt: 2.5 }}>
        {options.map((option) => {
          const selected = value === option.value;

          return (
            <Box
              key={option.value}
              onClick={() => onChange(option.value)}
              sx={{
                p: 1.75,

                display: "flex",
                alignItems: "center",

                gap: 1.5,

                borderRadius: "14px",

                border: selected ? "1px solid #2563EB" : "1px solid #E2E8F0",

                backgroundColor: selected ? "#EFF6FF" : "#FFFFFF",

                cursor: "pointer",

                "&:hover": {
                  borderColor: "#93C5FD",
                  backgroundColor: "#F8FBFF",
                },
              }}
            >
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography sx={TYPOGRAPHY.cardTitle}>
                  {option.title}
                </Typography>

                <Typography
                  sx={{
                    ...TYPOGRAPHY.bodySmall,
                    mt: 0.25,
                  }}
                >
                  {option.description}
                </Typography>
              </Box>

              <Box
                sx={{
                  width: 20,
                  height: 20,

                  flexShrink: 0,

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  borderRadius: "50%",

                  border: selected ? "6px solid #2563EB" : "2px solid #CBD5E1",

                  backgroundColor: "#FFFFFF",
                }}
              />
            </Box>
          );
        })}
      </Stack>
    </Box>
  );
}

function ReviewStep({ form }) {
  const account = MOCK_INSTAGRAM_ACCOUNTS.find(
    (item) => item.id === form.organizationId,
  );

  const content = MOCK_INSTAGRAM_CONTENT.find(
    (item) => item.id === form.contentId,
  );

  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>Review Automation</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        Review the automation details before creating it.
      </Typography>

      <Stack spacing={1.25} sx={{ mt: 2.5 }}>
        <ReviewRow label="Automation Name" value={form.name} />

        <ReviewRow
          label="Instagram Account"
          value={
            account ? `${account.organization} · ${account.username}` : "—"
          }
        />

        <ReviewRow
          label="Content"
          value={content ? `${content.title} · ${content.type}` : "—"}
        />

        <ReviewRow
          label="Trigger"
          value={
            form.triggerType === "Keyword"
              ? `Keyword: "${form.triggerValue}"`
              : form.triggerType || "—"
          }
        />

        <ReviewRow label="Reply" value={form.replyMessage} />

        <ReviewRow
          label="Status"
          value={form.status === "active" ? "Active" : "Disabled"}
        />
      </Stack>
    </Box>
  );
}

function ReviewRow({ label, value }) {
  return (
    <Box
      sx={{
        p: 1.5,

        borderRadius: "12px",

        backgroundColor: "#F8FAFC",

        border: "1px solid #E2E8F0",
      }}
    >
      <Typography sx={TYPOGRAPHY.caption}>{label}</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.body,
          mt: 0.25,

          color: "#1E293B",

          wordBreak: "break-word",
        }}
      >
        {value || "—"}
      </Typography>
    </Box>
  );
}
/* ============================================================
   TEMPORARY STEP PLACEHOLDER
============================================================ */

function PlaceholderStep({ title, description }) {
  return (
    <Box>
      <Typography sx={TYPOGRAPHY.sectionTitle}>{title}</Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.sectionDescription,
          mt: 0.5,
        }}
      >
        {description}
      </Typography>
    </Box>
  );
}
