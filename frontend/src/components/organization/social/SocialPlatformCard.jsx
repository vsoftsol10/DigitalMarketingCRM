// import { Box, Typography } from "@mui/material";

// import InstagramIcon from "@mui/icons-material/Instagram";
// import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
// import LinkedInIcon from "@mui/icons-material/LinkedIn";
// import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
// import YouTubeIcon from "@mui/icons-material/YouTube";
// import XIcon from "@mui/icons-material/X";

// const iconMap = {
//   instagram: InstagramIcon,
//   facebook: FacebookRoundedIcon,
//   linkedin: LinkedInIcon,
//   threads: SmartToyOutlinedIcon,
//   youtube: YouTubeIcon,
//   x: XIcon,
// };

// export default function SocialPlatformCard({
//   icon,
//   name,
//   backgroundColor,
//   iconColor,
//   selected = false,
//   disabled = false,
//   onClick,
// }) {
//   const Icon = iconMap[icon];

//   return (
//     <Box
//       // onClick={onClick}
//       onClick={!disabled ? onClick : undefined}
//       sx={{
//         flex: "1 1 0",
//         minWidth: 120,
//         maxWidth: 140,

//         height: 96,

//         borderRadius: "16px",

//         border: selected ? "2px solid #2563EB" : "1px solid #E2E8F0",

//         bgcolor: selected ? "#F8FBFF" : "#FFFFFF",

//         display: "flex",
//         flexDirection: "column",
//         justifyContent: "center",
//         alignItems: "center",

//         // cursor: "pointer",
//         cursor: disabled ? "not-allowed" : "pointer",

//         opacity: disabled ? 0.45 : 1,

//         pointerEvents: disabled ? "none" : "auto",

//         transition: "all .25s ease",

//         // "&:hover": {
//         //   borderColor: "#2563EB",
//         //   bgcolor: "#F8FBFF",
//         //   transform: "translateY(-2px)",
//         //   boxShadow: "0 8px 20px rgba(15,23,42,.06)",
//         // },
//         "&:hover": disabled
//           ? {}
//           : {
//               borderColor: "#2563EB",
//               bgcolor: "#F8FBFF",
//               transform: "translateY(-2px)",
//               boxShadow: "0 8px 20px rgba(15,23,42,.06)",
//             },
//       }}
//     >
//       <Box
//         sx={{
//           width: 40,
//           height: 40,

//           borderRadius: "12px",

//           bgcolor: backgroundColor,

//           display: "flex",
//           justifyContent: "center",
//           alignItems: "center",

//           mb: 1.5,
//         }}
//       >
//         {Icon && (
//           <Icon
//             sx={{
//               fontSize: 22,
//               color: iconColor,
//             }}
//           />
//         )}
//       </Box>

//       <Typography
//         sx={{
//           fontSize: "14px",
//           fontWeight: 500,
//           color: "#475569",
//         }}
//       >
//         {name}
//       </Typography>
//     </Box>
//   );
// }
import { Box, Typography } from "@mui/material";

import InstagramIcon from "@mui/icons-material/Instagram";
import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import YouTubeIcon from "@mui/icons-material/YouTube";
import XIcon from "@mui/icons-material/X";
import ApartmentRoundedIcon from "@mui/icons-material/ApartmentRounded";

const iconMap = {
  instagram: InstagramIcon,
  facebook: FacebookRoundedIcon,
  linkedin: LinkedInIcon,
  threads: SmartToyOutlinedIcon,
  youtube: YouTubeIcon,
  x: XIcon,
};

export default function SocialPlatformCard({
  icon,
  name,
  backgroundColor,
  iconColor,
  selected = false,
  disabled = false,
  onClick,
}) {
  const Icon = iconMap[icon] || ApartmentRoundedIcon;

  const handleClick = () => {
    if (disabled || typeof onClick !== "function") {
      return;
    }

    onClick();
  };

  // Cards act like buttons here (click to select a platform),
  // so they need keyboard support: Enter and Space both trigger
  // the same action a mouse click would.
  const handleKeyDown = (event) => {
    if (disabled) {
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleClick();
    }
  };

  return (
    <Box
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-pressed={selected}
      aria-disabled={disabled}
      aria-label={name}
      sx={{
        flex: "1 1 0",
        minWidth: 120,
        maxWidth: 140,

        height: 96,

        borderRadius: "16px",

        border: selected ? "2px solid #2563EB" : "1px solid #E2E8F0",

        bgcolor: selected ? "#F8FBFF" : "#FFFFFF",

        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",

        cursor: disabled ? "not-allowed" : "pointer",

        opacity: disabled ? 0.45 : 1,

        pointerEvents: disabled ? "none" : "auto",

        transition: "all .25s ease",

        "&:focus-visible": {
          outline: "2px solid #2563EB",
          outlineOffset: "2px",
        },

        "&:hover": disabled
          ? {}
          : {
              borderColor: "#2563EB",
              bgcolor: "#F8FBFF",
              transform: "translateY(-2px)",
              boxShadow: "0 8px 20px rgba(15,23,42,.06)",
            },
      }}
    >
      <Box
        aria-hidden="true"
        sx={{
          width: 40,
          height: 40,

          borderRadius: "12px",

          bgcolor: backgroundColor,

          display: "flex",
          justifyContent: "center",
          alignItems: "center",

          mb: 1.5,
        }}
      >
        <Icon
          sx={{
            fontSize: 22,
            color: iconColor,
          }}
        />
      </Box>

      <Typography
        sx={{
          fontSize: "14px",
          fontWeight: 500,
          color: "#475569",
        }}
      >
        {name}
      </Typography>
    </Box>
  );
}
