import {
  Alert,
  Avatar,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import FacebookRoundedIcon from "@mui/icons-material/FacebookRounded";
import InstagramIcon from "@mui/icons-material/Instagram";

import { useEffect, useMemo, useState } from "react";

// ============================================================
// COMPONENT
// ============================================================
//
// Page-first Meta connection:
//
// Facebook Page
//      ↓
// linked Instagram Professional Account
//
// User selects Facebook Pages only.
// Linked Instagram accounts are automatically included.
//
// ============================================================

export default function MetaPageSelectionDialog({
  open,
  data,
  loading = false,
  error = "",
  confirming = false,
  onClose,
  onConfirm,
}) {
  const [selectedPageIds, setSelectedPageIds] =
    useState([]);

  // ==========================================================
  // RESET SELECTION
  // ==========================================================

  useEffect(() => {
    if (!open) {
      setSelectedPageIds([]);
      return;
    }

    const pages = Array.isArray(data?.pages)
      ? data.pages
      : [];

    setSelectedPageIds(
      pages.map((page) =>
        String(
          page.platform_account_id,
        ),
      ),
    );
  }, [open, data]);

  // ==========================================================
  // DATA
  // ==========================================================

  const pages = Array.isArray(data?.pages)
    ? data.pages
    : [];

  const instagramAccounts =
    Array.isArray(data?.instagram_accounts)
      ? data.instagram_accounts
      : [];

  // ==========================================================
  // INSTAGRAM LOOKUP
  // ==========================================================

  const instagramByPage = useMemo(() => {
    const map = new Map();

    instagramAccounts.forEach((instagram) => {
      const pageId = String(
        instagram.linked_facebook_page_platform_account_id ||
          "",
      );

      if (!pageId) {
        return;
      }

      if (!map.has(pageId)) {
        map.set(pageId, []);
      }

      map.get(pageId).push(
        instagram,
      );
    });

    return map;
  }, [instagramAccounts]);

  // ==========================================================
  // TOGGLE PAGE
  // ==========================================================

  const handleTogglePage = (
    pageId,
  ) => {
    const normalizedPageId =
      String(pageId);

    setSelectedPageIds((current) => {
      if (
        current.includes(
          normalizedPageId,
        )
      ) {
        return current.filter(
          (id) =>
            id !== normalizedPageId,
        );
      }

      return [
        ...current,
        normalizedPageId,
      ];
    });
  };

  // ==========================================================
  // CONFIRM
  // ==========================================================

  const handleConfirm = () => {
    if (
      selectedPageIds.length === 0 ||
      typeof onConfirm !== "function"
    ) {
      return;
    }

    onConfirm(
      selectedPageIds,
    );
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <Dialog
      open={open}
      onClose={
        confirming
          ? undefined
          : onClose
      }
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle
        sx={{
          pb: 1,
          fontWeight: 700,
        }}
      >
        Select Facebook Pages
      </DialogTitle>

      <DialogContent>
        {/* ==================================================
            LOADING
        ================================================== */}

        {loading && (
          <Box
            sx={{
              py: 6,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CircularProgress size={28} />
          </Box>
        )}

        {/* ==================================================
            ERROR
        ================================================== */}

        {!loading && error && (
          <Alert
            severity="error"
            sx={{
              mt: 1,
            }}
          >
            {error}
          </Alert>
        )}

        {/* ==================================================
            CONTENT
        ================================================== */}

        {!loading &&
          !error &&
          pages.length === 0 && (
            <Alert
              severity="info"
              sx={{
                mt: 1,
              }}
            >
              No Facebook Pages are available
              for this Meta account.
            </Alert>
          )}

        {!loading &&
          !error &&
          pages.length > 0 && (
            <Stack
              spacing={1.5}
              sx={{
                mt: 1,
              }}
            >
              <Typography
                sx={{
                  fontSize: 14,
                  color: "#64748B",
                  lineHeight: 1.5,
                  mb: 1,
                }}
              >
                Select the Facebook Page(s)
                you want to connect. Any linked
                Instagram Professional account
                will be connected automatically.
              </Typography>

              {pages.map((page) => {
                const pageId = String(
                  page.platform_account_id,
                );

                const selected =
                  selectedPageIds.includes(
                    pageId,
                  );

                const linkedInstagram =
                  instagramByPage.get(
                    pageId,
                  ) || [];

                return (
                  <Box
                    key={pageId}
                    onClick={() =>
                      !confirming &&
                      handleTogglePage(
                        pageId,
                      )
                    }
                    sx={{
                      border: "1px solid",
                      borderColor: selected
                        ? "#2563EB"
                        : "#E2E8F0",
                      borderRadius: "14px",
                      px: 1.5,
                      py: 1.5,
                      cursor: confirming
                        ? "default"
                        : "pointer",
                      bgcolor: selected
                        ? "#F8FBFF"
                        : "#FFFFFF",
                      transition:
                        "border-color .2s ease, background-color .2s ease",
                    }}
                  >
                    {/* ======================================
                        FACEBOOK PAGE
                    ====================================== */}

                    <Stack
                      direction="row"
                      spacing={1.5}
                      alignItems="center"
                    >
                      <Checkbox
                        checked={selected}
                        disabled={
                          confirming
                        }
                        onChange={() =>
                          handleTogglePage(
                            pageId,
                          )
                        }
                        onClick={(event) =>
                          event.stopPropagation()
                        }
                      />

                      <Avatar
                        sx={{
                          width: 42,
                          height: 42,
                          bgcolor:
                            "#EFF6FF",
                          color:
                            "#2563EB",
                        }}
                      >
                        <FacebookRoundedIcon />
                      </Avatar>

                      <Box
                        sx={{
                          minWidth: 0,
                          flex: 1,
                        }}
                      >
                        <Typography
                          sx={{
                            fontSize: 15,
                            fontWeight: 600,
                            color:
                              "#1E293B",
                          }}
                        >
                          {page.name ||
                            "Facebook Page"}
                        </Typography>

                        <Typography
                          sx={{
                            mt: 0.25,
                            fontSize: 12,
                            color:
                              "#94A3B8",
                          }}
                        >
                          Facebook Page
                        </Typography>
                      </Box>
                    </Stack>

                    {/* ====================================
                        LINKED INSTAGRAM
                    ==================================== */}

                    {linkedInstagram.length >
                      0 && (
                      <>
                        <Divider
                          sx={{
                            my: 1.5,
                          }}
                        />

                        <Stack
                          spacing={1}
                          sx={{
                            pl: 7,
                          }}
                        >
                          {linkedInstagram.map(
                            (instagram) => (
                              <Stack
                                key={
                                  instagram.platform_account_id
                                }
                                direction="row"
                                spacing={1}
                                alignItems="center"
                              >
                                <InstagramIcon
                                  sx={{
                                    fontSize: 20,
                                    color:
                                      "#C13584",
                                  }}
                                />

                                <Box>
                                  <Typography
                                    sx={{
                                      fontSize: 13,
                                      fontWeight: 600,
                                      color:
                                        "#334155",
                                    }}
                                  >
                                    {instagram.name ||
                                      instagram.account_name ||
                                      "Instagram"}
                                  </Typography>

                                  {instagram.username && (
                                    <Typography
                                      sx={{
                                        fontSize: 12,
                                        color:
                                          "#64748B",
                                      }}
                                    >
                                      @
                                      {
                                        instagram.username
                                      }
                                    </Typography>
                                  )}
                                </Box>

                                <Typography
                                  sx={{
                                    ml: "auto",
                                    fontSize: 11,
                                    fontWeight: 600,
                                    color:
                                      "#059669",
                                  }}
                                >
                                  Linked
                                </Typography>
                              </Stack>
                            ),
                          )}
                        </Stack>
                      </>
                    )}

                    {/* ====================================
                        NO INSTAGRAM
                    ==================================== */}

                    {linkedInstagram.length ===
                      0 && (
                      <Typography
                        sx={{
                          pl: 7,
                          mt: 1,
                          fontSize: 12,
                          color:
                            "#94A3B8",
                        }}
                      >
                        No linked Instagram
                        Professional account
                        found.
                      </Typography>
                    )}
                  </Box>
                );
              })}
            </Stack>
          )}
      </DialogContent>

      <DialogActions
        sx={{
          px: 3,
          pb: 2.5,
          pt: 1,
        }}
      >
        <Button
          type="button"
          onClick={onClose}
          disabled={confirming}
          sx={{
            textTransform: "none",
            color: "#64748B",
            fontWeight: 600,
          }}
        >
          Cancel
        </Button>

        <Button
          type="button"
          variant="contained"
          onClick={handleConfirm}
          disabled={
            loading ||
            confirming ||
            selectedPageIds.length === 0
          }
          startIcon={
            confirming ? (
              <CircularProgress
                size={15}
                color="inherit"
              />
            ) : null
          }
          sx={{
            textTransform: "none",
            fontWeight: 600,
            borderRadius: "10px",
            px: 2.5,
          }}
        >
          {confirming
            ? "Connecting..."
            : "Connect Selected"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}