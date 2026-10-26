import { useFormContext } from "react-hook-form";

import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import CalendarMonthRoundedIcon from "@mui/icons-material/CalendarMonthRounded";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";

import PrimaryButton from "../../../ui/button/PrimaryButton";

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
      sx={{
        borderRadius: "17px",
        border: "1px solid rgba(255,255,255,.7)",
        background:
          "linear-gradient(115deg, #A96BEA 0%, #7074ED 54%, #4A91ED 100%)",
        boxShadow:
          "0 11px 22px rgba(100,92,203,.3), 0 3px 7px rgba(65,101,210,.17), inset 0 1px 0 rgba(255,255,255,.46), inset 0 -2px 3px rgba(67,71,163,.16)",
        "&:hover": {
          background:
            "linear-gradient(115deg, #9D60E3 0%, #5E70E8 56%, #3D8FEA 100%)",
          boxShadow:
            "0 13px 24px rgba(100,92,203,.34), 0 3px 8px rgba(65,101,210,.2), inset 0 1px 0 rgba(255,255,255,.42)",
        },
        "&:focus-visible": {
          outline: "2px solid #7E8FE8",
          outlineOffset: 3,
        },
        "&.Mui-disabled": {
          color: "rgba(255,255,255,.78)",
          background: "linear-gradient(115deg, #B993DD, #929BE1)",
        },
      }}
    >
      {action.label}
    </PrimaryButton>
  );
}
