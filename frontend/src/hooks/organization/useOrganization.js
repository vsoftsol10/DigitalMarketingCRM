import { useEffect, useState } from "react";

export default function useOrganization() {
  const [organization, setOrganization] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);

  useEffect(() => {
    /*
      Backend later
    */
  }, []);

  return {
    organization,
    loading,
    error,
  };
}