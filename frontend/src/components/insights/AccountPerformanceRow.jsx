import { Avatar, Box, TableCell, TableRow, Typography } from "@mui/material";

import PlatformBadge from "./PlatformBadge";
import TrendSparkline from "./TrendSparkline";
import formatCompactNumber from "../../utils/formatters/formatCompactNumber";

export default function AccountPerformanceRow({ account }) {
  return (
    <TableRow
      hover
      sx={{
        "& td": {
          borderBottom: "1px solid #F1F5F9",
          py: 2,
        },

        "&:last-child td": {
          borderBottom: "none",
        },
      }}
    >
      {/* Account */}

      <TableCell sx={{ pl: 0 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <Avatar
            sx={{
              width: 42,
              height: 42,

              bgcolor: account.avatar_color,

              fontSize: 15,
              fontWeight: 700,
            }}
          >
            {account.avatar}
          </Avatar>

          <Box>
            <Typography
              sx={{
                fontSize: 15,
                fontWeight: 600,
                color: "#0F172A",
              }}
            >
              {account.account_name}
            </Typography>

            <Typography
              sx={{
                mt: 0.25,

                fontSize: 13,

                color: "#64748B",
              }}
            >
              {account.organization}
            </Typography>
          </Box>
        </Box>
      </TableCell>

      {/* Platform */}

      <TableCell>
        <PlatformBadge platform={account.platform} />
      </TableCell>

      {/* Followers */}

      <TableCell align="right">
        <Typography
          sx={{
            fontSize: 15,
            fontWeight: 600,
          }}
        >
          {/* {account.followers} */}
          {formatCompactNumber(account.followers)}
        </Typography>
      </TableCell>

      {/* Engagement */}

      <TableCell align="right">
        <Typography
          sx={{
            fontSize: 15,
            fontWeight: 600,
          }}
        >
          {account.engagement_rate}%
        </Typography>
      </TableCell>

      {/* Reach */}

      <TableCell align="right">
        <Typography
          sx={{
            fontSize: 15,
            fontWeight: 600,
          }}
        >
          {/* {account.reach} */}
          {formatCompactNumber(account.reach)}
        </Typography>
      </TableCell>

      {/* Trend */}

      <TableCell align="center" sx={{ pr: 0 }}>
        <TrendSparkline data={account.trend} />
      </TableCell>
    </TableRow>
  );
}
