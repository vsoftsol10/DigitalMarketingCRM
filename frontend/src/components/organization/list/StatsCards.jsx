import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
} from "@mui/material";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function StatsCards({
  items = [],
}) {
  return (
    <Grid
      container
      spacing={3}
      sx={{
        mb: 5,
      }}
    >
      {items.map((item) => {
        const Icon = item.icon;

        return (
          <Grid
            key={item.title}
            size={{ xs: 12, sm: 6, lg: 3 }}
          >
            <Card
              elevation={0}
              sx={{
                height: 140,
                borderRadius: "18px",
                border: "1px solid #E2E8F0",
                bgcolor: "#FFFFFF",
              }}
            >
              <CardContent
                sx={{
                  p: 3,
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",

                  "&:last-child": {
                    pb: 3,
                  },
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                  }}
                >
                  {Icon && (
                    <Icon
                      sx={{
                        fontSize: 20,
                        color: "#64748B",
                      }}
                    />
                  )}

                  <Typography sx={TYPOGRAPHY.statTitle}>
                    {item.title}
                  </Typography>
                </Box>

                <Typography
                  sx={{
                    ...TYPOGRAPHY.statValue,
                    mt: 1,
                  }}
                >
                  {item.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );
}