import {
  Box,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

import ContentCopyOutlinedIcon from "@mui/icons-material/ContentCopyOutlined";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";

import toast from "react-hot-toast";

import SecondaryButton from "../../../ui/button/SecondaryButton";
import PrimaryButton from "../../../ui/button/PrimaryButton";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function AISuggestionCard({
  suggestion,
  onUse,
}) {
  async function handleCopy() {
    await navigator.clipboard.writeText(
      suggestion.caption
    );

    toast.success("Caption copied");
  }

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        border: "1px solid #E2E8F0",
        borderRadius: "18px",
      }}
    >
      <Typography
        sx={{
          ...TYPOGRAPHY.cardTitle,
          mb: 1,
        }}
      >
        {suggestion.title}
      </Typography>

      <Typography
        sx={{
          ...TYPOGRAPHY.body,
          whiteSpace: "pre-wrap",
        }}
      >
        {suggestion.caption}
      </Typography>

      <Stack
        direction="row"
        spacing={2}
        sx={{
          mt: 3,
        }}
      >
        <PrimaryButton
          fullWidth
          startIcon={
            <CheckCircleOutlineRoundedIcon />
          }
          onClick={() => onUse(suggestion)}
        >
          Use Caption
        </PrimaryButton>

        <SecondaryButton
          fullWidth
          startIcon={
            <ContentCopyOutlinedIcon />
          }
          onClick={handleCopy}
        >
          Copy
        </SecondaryButton>
      </Stack>
    </Paper>
  );
}