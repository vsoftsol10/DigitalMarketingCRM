// import React from "react";
// import ReactDOM from "react-dom/client";
// import { Toaster } from "react-hot-toast";

// import App from "./App";

// import QueryProvider from "./providers/QueryProvider";
// import { AuthProvider } from "./context/AuthContext";
// import { ThemeProvider } from "@mui/material/styles";
// import CssBaseline from "@mui/material/CssBaseline";

// import theme from "./theme/theme";

// ReactDOM.createRoot(document.getElementById("root")).render(
//   <React.StrictMode>
//     <QueryProvider>
//       <ThemeProvider theme={theme}>
//         <CssBaseline />

//         <AuthProvider>
//           <App />

//           <Toaster position="top-right" reverseOrder={false} />
//         </AuthProvider>
//       </ThemeProvider>
//     </QueryProvider>
//   </React.StrictMode>,
// );

import React from "react";
import ReactDOM from "react-dom/client";

import { Toaster } from "react-hot-toast";

import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";

import {
  LocalizationProvider,
} from "@mui/x-date-pickers";

import {
  AdapterDayjs,
} from "@mui/x-date-pickers/AdapterDayjs";

import App from "./App";

import theme from "./theme/theme";

import QueryProvider from "./providers/QueryProvider";

import { AuthProvider } from "./context/AuthContext";

ReactDOM.createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>
    <QueryProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />

        <LocalizationProvider
          dateAdapter={AdapterDayjs}
        >
          <AuthProvider>
            <App />

            <Toaster
              position="top-right"
              reverseOrder={false}
            />
          </AuthProvider>
        </LocalizationProvider>
      </ThemeProvider>
    </QueryProvider>
  </React.StrictMode>
);