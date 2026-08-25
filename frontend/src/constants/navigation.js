import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";

import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import SendOutlinedIcon from "@mui/icons-material/SendOutlined";
import CalendarMonthOutlinedIcon from "@mui/icons-material/CalendarMonthOutlined";

import ChatBubbleOutlineOutlinedIcon from "@mui/icons-material/ChatBubbleOutlineOutlined";
import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";

import InsightsOutlinedIcon from "@mui/icons-material/InsightsOutlined";

import CreditCardOutlinedIcon from "@mui/icons-material/CreditCardOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";

export const navigation = [
  {
    title: "OVERVIEW",
    items: [
      {
        label: "Dashboard",
        path: "/",
        icon: DashboardOutlinedIcon,
      },
    ],
  },

  {
    title: "CLIENTS",
    items: [
      {
        label: "Organizations",
        path: "/organizations",
        icon: BusinessOutlinedIcon,
      },
    ],
  },

  {
    title: "CONTENT",
    items: [
      {
        label: "Content Planner",
        path: "/planner",
        icon: AutoAwesomeOutlinedIcon,
      },
      // {
      //   label: "AI Script",
      //   path: "/ai-scripts",
      //   icon: SmartToyOutlinedIcon,
      // },
      {
        label: "Create Post",
        path: "/posts",
        icon: SendOutlinedIcon,
      },
      {
        label: "Calendar",
        path: "/calendar",
        icon: CalendarMonthOutlinedIcon,
      },
    ],
  },

  {
    title: "ENGAGE",
    items: [
      {
        label: "DM Automation",
        path: "/dm-automation",
        icon: ChatBubbleOutlineOutlinedIcon,
      },
      {
        label: "Ads",
        path: "/ads",
        icon: CampaignOutlinedIcon,
      },
    ],
  },

  {
    title: "ANALYZE",
    items: [
      {
        label: "Insights",
        path: "/insights",
        icon: InsightsOutlinedIcon,
      },
    ],
  },

  {
    title: "SYSTEM",
    items: [
      {
        label: "Plans",
        path: "/plans",
        icon: CreditCardOutlinedIcon,
      },
      {
        label: "Settings",
        path: "/settings",
        icon: SettingsOutlinedIcon,
      },
    ],
  },
];
