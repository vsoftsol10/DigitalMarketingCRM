import { Box, Button, Paper, Stack, Typography } from "@mui/material";

import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";

import { TYPOGRAPHY } from "../../theme/typography";

export default function SignOutSettings({ onLogout, loading = false }) {
  return (
    <Paper
      elevation={0}
      sx={{
        width: "100%",

        border: "1px solid",
        borderColor: "error.light",

        borderRadius: 3,

        bgcolor: "background.paper",

        overflow: "hidden",

        boxSizing: "border-box",
      }}
    >
      <Box
        sx={{
          px: {
            xs: 2.5,
            sm: 3,
          },

          py: {
            xs: 2.5,
            sm: 3,
          },
        }}
      >
        <Stack
          direction={{
            xs: "column",
            sm: "row",
          }}
          alignItems={{
            xs: "flex-start",
            sm: "center",
          }}
          justifyContent="space-between"
          spacing={{
            xs: 2.5,
            sm: 2,
          }}
          sx={{
            width: "100%",
          }}
        >
          {/* ======================================
              LEFT CONTENT
          ====================================== */}

          <Stack
            direction="row"
            alignItems="center"
            spacing={{
              xs: 1.5,
              sm: 1.75,
            }}
            sx={{
              minWidth: 0,
              flex: 1,
            }}
          >
            {/* ==================================
                LOGOUT ICON
            ================================== */}

            <Box
              sx={{
                width: 48,
                height: 48,

                display: "flex",
                alignItems: "center",
                justifyContent: "center",

                flexShrink: 0,

                borderRadius: 2,

                bgcolor: "error.50",

                color: "error.main",
              }}
            >
              <LogoutRoundedIcon
                sx={{
                  fontSize: 23,
                }}
              />
            </Box>

            {/* ==================================
                TEXT
            ================================== */}

            <Box
              sx={{
                minWidth: 0,
              }}
            >
              <Typography
                component="h2"
                sx={{
                  ...TYPOGRAPHY.cardTitle,

                  color: "text.primary",

                  lineHeight: 1.35,
                }}
              >
                Sign out
              </Typography>

              <Typography
                component="p"
                sx={{
                  ...TYPOGRAPHY.bodySmall,

                  color: "text.secondary",

                  mt: 0.35,

                  lineHeight: 1.5,
                }}
              >
                Log out of your CRM account.
              </Typography>
            </Box>
          </Stack>

          {/* ======================================
              LOGOUT BUTTON
          ====================================== */}

          {/* <Button
            type="button"
            variant="contained"
            color="error"
            disableElevation
            disabled={loading}
            startIcon={
              <LogoutRoundedIcon
                sx={{
                  fontSize: 20,
                }}
              />
            }
            onClick={onLogout}
            sx={{
              minWidth: {
                xs: "100%",
                sm: 110,
              },

              height: 44,

              px: 2.5,

              borderRadius: 2,

              flexShrink: 0,

              ...TYPOGRAPHY.button,

              fontWeight: 600,

              alignSelf: {
                xs: "stretch",
                sm: "center",
              },
            }}
          >
            {loading
              ? "Signing out..."
              : "Logout"}
          </Button> */}
          <Button
            type="button"
            variant="contained"
            color="error"
            disableElevation
            disabled={loading}
            startIcon={
              <LogoutRoundedIcon
                sx={{
                  fontSize: 20,
                }}
              />
            }
            onClick={onLogout}
            sx={{
              minWidth: {
                xs: "100%",
                sm: 110,
              },

              height: 44,

              px: 2.5,

              borderRadius: 2,

              flexShrink: 0,

              ...TYPOGRAPHY.button,

              fontWeight: 600,

              alignSelf: {
                xs: "stretch",
                sm: "center",
              },
            }}
          >
            {loading ? "Signing out..." : "Logout"}
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}
