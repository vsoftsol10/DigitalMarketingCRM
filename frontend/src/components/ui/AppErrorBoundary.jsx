import { Component } from "react";

import ErrorState from "./ErrorState";

function safeErrorType(error) {
  const name = typeof error?.name === "string" ? error.name : "Error";
  return /^[A-Za-z][A-Za-z0-9]{0,60}$/.test(name) ? name : "Error";
}

export default class AppErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    const componentCount = (info?.componentStack?.match(/\n\s+in /g) || []).length;
    console.error("Application rendering error", {
      errorType: safeErrorType(error),
      componentCount,
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorState
          title="We couldn't display this page"
          message="An unexpected problem interrupted the page. Reload the application to try again."
          retryLabel="Reload page"
          onRetry={() => window.location.reload()}
          variant="page"
        />
      );
    }

    return this.props.children;
  }
}
