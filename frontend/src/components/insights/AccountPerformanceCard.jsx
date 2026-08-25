import {
  Card,
  CardContent,
  Typography,
} from "@mui/material";

import AccountPerformanceTable from "./AccountPerformanceTable";

export default function AccountPerformanceCard({
  accounts = [],
}) {
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "22px",
      }}
    >
      <CardContent
        sx={{
          p: 3,

          "&:last-child": {
            pb: 3,
          },
        }}
      >
        {/* Header */}

        <Typography
          sx={{
            fontSize: 18,
            fontWeight: 700,
            color: "#1E293B",
          }}
        >
          Account performance
        </Typography>

        <Typography
          sx={{
            mt: 0.5,
            mb: 4,

            fontSize: 15,
            color: "#64748B",
          }}
        >
          {accounts.length} connected accounts
        </Typography>

        <AccountPerformanceTable
          accounts={accounts}
        />
      </CardContent>
    </Card>
  );
}