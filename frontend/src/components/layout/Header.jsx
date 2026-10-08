import { useMemo, useRef, useState } from "react";
import {
  AppBar,
  Toolbar,
  Box,
  Avatar,
  TextField,
  InputAdornment,
  ClickAwayListener,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";
import { useNavigate } from "react-router-dom";
import { navigation } from "../../constants/navigation";
import { useAuthContext } from "../../context/AuthContext";
import HeaderNotificationCenter from "./HeaderNotificationCenter";

const searchablePages = navigation.flatMap((section) => section.items.map((item) => ({
  ...item,
  section: section.title,
})));

export default function Header() {
  const navigate = useNavigate();
  const { user } = useAuthContext();
  const searchInputRef = useRef(null);
  const [searchValue, setSearchValue] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const matchingPages = useMemo(() => {
    const query = searchValue.trim().toLocaleLowerCase();
    if (!query) return [];
    return searchablePages.filter((page) => page.label.toLocaleLowerCase().includes(query));
  }, [searchValue]);

  function navigateToPage(page) {
    navigate(page.path);
    setSearchValue("");
    setSearchOpen(false);
    searchInputRef.current?.blur();
  }

  return (
    <AppBar
      position="sticky"
      elevation={0}
      color="inherit"
      sx={{
        bgcolor: "#FFFFFF",
        borderBottom: "1px solid #E5E7EB",
      }}
    >
      <Toolbar
        sx={{
          height: 80,
          px: "32px !important",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        {/* Left */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          {/* <HomeOutlinedIcon
            sx={{
              fontSize: 20,
              color: "#64748B",
            }}
          />

          <Typography
            sx={{
              fontSize: 16,
              fontWeight: 600,
              color: "#1E293B",
            }}
          >
            Dashboard
          </Typography> */}
        </Box>

        {/* Right */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2.5,
          }}
        >
          <ClickAwayListener onClickAway={() => setSearchOpen(false)}>
            <Box sx={{ position: "relative", width: 400 }}>
              <TextField
                inputRef={searchInputRef}
                fullWidth
                size="small"
                placeholder="Search..."
                value={searchValue}
                onChange={(event) => {
                  const value = event.target.value;
                  setSearchValue(value);
                  setSearchOpen(Boolean(value.trim()));
                }}
                onFocus={() => setSearchOpen(Boolean(searchValue.trim()))}
                onKeyDown={(event) => {
                  if (event.key === "Escape") setSearchOpen(false);
                  if (event.key === "Enter" && matchingPages.length) {
                    event.preventDefault();
                    navigateToPage(matchingPages[0]);
                  }
                }}
                sx={{
                  width: 400,

                  "& .MuiOutlinedInput-root": {
                    height: 46,
                    borderRadius: "18px",
                    bgcolor: "#F8FAFC",

                    "& fieldset": {
                      border: "none",
                    },

                    "&:hover fieldset": {
                      border: "none",
                    },

                    "&.Mui-focused fieldset": {
                      border: "1px solid #2563EB",
                    },
                  },

                  "& input": {
                    fontSize: 15,
                  },
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon
                        sx={{
                          color: "#94A3B8",
                        }}
                      />
                    </InputAdornment>
                  ),
                }}
              />
              {searchOpen && matchingPages.length > 0 && (
                <Paper
                  elevation={6}
                  sx={{
                    position: "absolute",
                    top: "calc(100% + 8px)",
                    left: 0,
                    right: 0,
                    zIndex: (theme) => theme.zIndex.modal,
                    maxHeight: 360,
                    overflowY: "auto",
                    border: "1px solid #E2E8F0",
                    borderRadius: "12px",
                  }}
                >
                  <List dense disablePadding>
                    {matchingPages.map((page) => {
                      const PageIcon = page.icon;
                      return (
                        <ListItemButton
                          key={page.path}
                          onClick={() => navigateToPage(page)}
                          sx={{ py: 1, px: 1.5 }}
                        >
                          <ListItemIcon sx={{ minWidth: 34, color: "#64748B" }}>
                            <PageIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={page.label}
                            secondary={page.section}
                            sx={{
                              "& .MuiListItemText-primary": { fontSize: 14, color: "#1E293B" },
                              "& .MuiListItemText-secondary": { fontSize: 10, color: "#64748B" },
                            }}
                          />
                        </ListItemButton>
                      );
                    })}
                  </List>
                </Paper>
              )}
            </Box>
          </ClickAwayListener>

          <HeaderNotificationCenter />

          <Avatar
            src={user?.profile_image || undefined}
            alt={user?.full_name || "Profile"}
            onClick={() => navigate("/settings")}
            sx={{
              width: 44,
              height: 44,
              bgcolor: "#2563EB",
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            AR
          </Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
