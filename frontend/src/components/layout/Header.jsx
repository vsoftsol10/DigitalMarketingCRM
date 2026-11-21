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

const SEARCH_ICON_COLORS = {
  "/": "#5B5DD4",
  "/organizations": "#3F70B8",
  "/planner": "#7951D2",
  "/posts": "#287FCF",
  "/calendar": "#168DB8",
  "/dm-automation": "#8756D7",
  "/ads": "#B84FC7",
  "/insights": "#3E78C5",
  "/plans": "#7586A5",
  "/settings": "#7586A5",
};

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
        borderBottom: "1px solid #DDE3F1",
        boxShadow: "none",
      }}
    >
      <Toolbar
        sx={{
          height: 80,
          px: { xs: "16px !important", md: "32px !important" },
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
            position: "relative",
            display: "flex",
            alignItems: "center",
            gap: 2.5,
            width: "100%",
            justifyContent: "flex-end",
          }}
        >
          <ClickAwayListener onClickAway={() => setSearchOpen(false)}>
            <Box sx={{ position: "absolute", left: 0, top: "50%", transform: "translateY(-50%)", width: { xs: 220, sm: 300, md: 448 }, maxWidth: "42vw", zIndex: (theme) => theme.zIndex.modal }}>
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
                  width: "100%",

                  "& .MuiOutlinedInput-root": {
                    height: 48,
                    borderRadius: "14px",
                    background: "#F7F8FC",
                    border: "1px solid #DCE2EF",
                    boxShadow: "none",
                    transition: "border-color .18s ease, box-shadow .18s ease",

                    "& fieldset": {
                      border: "none",
                    },

                    "&:hover fieldset": {
                      border: "none",
                    },

                    "&:hover": {
                      borderColor: "rgba(125,145,198,.42)",
                    },

                    "&.Mui-focused": {
                      borderColor: "rgba(89,116,220,.6)",
                      boxShadow: "0 7px 16px rgba(79,99,157,.12), 0 0 0 3px rgba(91,116,220,.11), inset 0 2px 4px rgba(94,111,159,.08), inset 0 1px 0 rgba(255,255,255,.98)",
                    },

                    "&.Mui-focused fieldset": {
                      border: "none",
                    },
                  },

                  "& input": {
                    fontSize: 15,
                    color: "#263754",
                    "&::placeholder": { color: "#8491AC", opacity: 1 },
                  },
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon
                        sx={{
                          color: "#7384AA",
                          fontSize: 21,
                          ml: 0.25,
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
                    maxHeight: "min(360px, calc(100vh - 100px))",
                    overflowY: "auto",
                    border: "1px solid rgba(255,255,255,.94)",
                    borderRadius: "16px",
                    background: "#FFFFFF",
                    boxShadow: "0 12px 28px rgba(31,41,80,.14)",
                    backdropFilter: "blur(18px)",
                    scrollbarWidth: "thin",
                    scrollbarColor: "rgba(122,143,190,.45) transparent",
                    "&::-webkit-scrollbar": { width: 7 },
                    "&::-webkit-scrollbar-thumb": { borderRadius: 8, background: "rgba(122,143,190,.38)" },
                  }}
                >
                  <List dense disablePadding sx={{ py: 0.6 }}>
                    {matchingPages.map((page) => {
                      const PageIcon = page.icon;
                      return (
                        <ListItemButton
                          key={page.path}
                          onClick={() => navigateToPage(page)}
                          sx={{
                            minHeight: 48,
                            mx: 0.6,
                            my: 0.25,
                            px: 1.4,
                            py: 0.85,
                            borderRadius: "11px",
                            color: "#263754",
                            "&:hover": { bgcolor: "rgba(218,231,255,.72)" },
                            "&.Mui-focusVisible": {
                              bgcolor: "rgba(218,231,255,.82)",
                              outline: "2px solid rgba(89,116,220,.42)",
                              outlineOffset: -2,
                            },
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 34, color: "#64748B" }}>
                            <PageIcon sx={{ fontSize: 19, color: SEARCH_ICON_COLORS[page.path] || "#7586A5", filter: "drop-shadow(0 1px 1px rgba(44,63,111,.14))" }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={page.label}
                            secondary={page.section}
                            sx={{
                              "& .MuiListItemText-primary": { fontSize: 14, fontWeight: 600, color: "#263754" },
                              "& .MuiListItemText-secondary": { fontSize: 10, fontWeight: 600, letterSpacing: 0.35, color: "#8290AD" },
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
              bgcolor: "#8247F5",
              color: "#FFFFFF",
              fontSize: 16,
              fontWeight: 700,
              border: "2px solid #FFFFFF",
              boxShadow: "0 3px 8px rgba(31,41,80,.12)",
              cursor: "pointer",
            }}
          >
            AR
          </Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
