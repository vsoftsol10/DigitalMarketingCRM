import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  TableCell,
} from "@mui/material";

import AccountPerformanceRow from "./AccountPerformanceRow";

export default function AccountPerformanceTable({
  accounts = [],
}) {
  return (
    <TableContainer>
      <Table>
        {/* Header */}

        <TableHead>
          <TableRow>
            <TableCell
              sx={headerCellStyle({
                width: "30%",
                pl: 0,
              })}
            >
              ACCOUNT
            </TableCell>

            <TableCell
              sx={headerCellStyle({
                width: "20%",
              })}
            >
              PLATFORM
            </TableCell>

            <TableCell
              align="right"
              sx={headerCellStyle({
                width: "14%",
              })}
            >
              FOLLOWERS
            </TableCell>

            <TableCell
              align="right"
              sx={headerCellStyle({
                width: "14%",
              })}
            >
              ENGAGEMENT
            </TableCell>

            <TableCell
              align="right"
              sx={headerCellStyle({
                width: "14%",
              })}
            >
              REACH
            </TableCell>

            <TableCell
              align="center"
              sx={headerCellStyle({
                width: "8%",
                pr: 0,
              })}
            >
              TREND
            </TableCell>
          </TableRow>
        </TableHead>

        {/* Body */}

        <TableBody>
          {accounts.map((account) => (
            <AccountPerformanceRow
              key={account.id}
              account={account}
            />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function headerCellStyle(extra = {}) {
  return {
    borderBottom: "1px solid #E2E8F0",

    color: "#94A3B8",

    fontSize: 13,

    fontWeight: 700,

    letterSpacing: "0.04em",

    py: 1.8,

    ...extra,
  };
}