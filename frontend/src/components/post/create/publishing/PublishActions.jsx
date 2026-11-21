import { useFormContext } from "react-hook-form";

import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import CalendarMonthRoundedIcon from "@mui/icons-material/CalendarMonthRounded";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";

import PrimaryButton from "../../../ui/button/PrimaryButton";
import { postPrimaryButtonSx } from "../postUiSx";

export default function PublishActions({ loading = false }) {
  const { watch } = useFormContext();

  const publishType = watch("publish_type");

  const actionConfig = {
    NOW: {
      label: "Publish Now",
      icon: <BoltRoundedIcon />,
    },

    SCHEDULE: {
      label: "Schedule Post",
      icon: <CalendarMonthRoundedIcon />,
    },

    DRAFT: {
      label: "Save as Draft",
      icon: <SaveOutlinedIcon />,
    },
  };

  const action = actionConfig[publishType] || actionConfig.NOW;

  return (
    <PrimaryButton
      type="submit"
      loading={loading}
      disabled={loading}
      startIcon={action.icon}
      sx={{ ...postPrimaryButtonSx, width: "100%" }}
    >
      {action.label}
    </PrimaryButton>
  );
}
