import { Box, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";
import { useNavigate } from "react-router-dom";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function Breadcrumb({
  items = [],
  showBack = true,
}) {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        mb: 3,
      }}
    >
      {showBack ? (
        <Box
          onClick={() => navigate(-1)}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 0.5,
            cursor: "pointer",
            color: "#64748B",

            "&:hover": {
              color: "#2563EB",
            },
          }}
        >
          <ArrowBackRoundedIcon sx={{ fontSize: 18 }} />

          <Typography sx={TYPOGRAPHY.breadcrumb}>
            Back
          </Typography>
        </Box>
      ) : (
        <Box />
      )}

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
        }}
      >
        {items.map((item, index) => {
          const Icon = item.icon;

          return (
            <Box
              key={item.label}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              {Icon && (
                <Icon
                  sx={{
                    fontSize: 18,
                    color: "#64748B",
                  }}
                />
              )}

              <Typography
                sx={
                  index === items.length - 1
                    ? TYPOGRAPHY.breadcrumbActive
                    : TYPOGRAPHY.breadcrumb
                }
              >
                {item.label}
              </Typography>

              {index !== items.length - 1 && (
                <ChevronRightRoundedIcon
                  sx={{
                    fontSize: 18,
                    color: "#94A3B8",
                  }}
                />
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}