import { useCallback, useEffect, useRef, useState } from "react";

import contentPlannerService from "../../services/contentPlanner.service";

const INITIAL_FILTERS = {
  search: "",
  organization: "all",
};

export default function useContentPlanner() {
  const [planner, setPlanner] = useState({
    statistics: {},
    organizations: [],
    ideas: [],
  });

  const [filters, setFilters] = useState(INITIAL_FILTERS);

  const [initialLoading, setInitialLoading] = useState(true);

  const [tableLoading, setTableLoading] = useState(false);

  const [error, setError] = useState(null);

  const requestSequenceRef = useRef(0);

  const loadPlanner = useCallback(
    async ({ nextFilters = filters, initial = false } = {}) => {
      const requestSequence = ++requestSequenceRef.current;

      try {
        if (initial) {
          setInitialLoading(true);
        } else {
          setTableLoading(true);
        }

        setError(null);

        const response = await contentPlannerService.getContentPlanner({
          search: nextFilters.search,
          organization: nextFilters.organization,
        });

        if (requestSequence !== requestSequenceRef.current) {
          return;
        }

        if (!response?.success) {
          throw new Error(
            response?.message || "Unable to load content planner.",
          );
        }

        if (!response?.data) {
          throw new Error("Content planner data was not returned.");
        }

        setPlanner(response.data);
      } catch (error) {
        if (requestSequence !== requestSequenceRef.current) {
          return;
        }

        console.error("Failed to load content planner:", error);

        setError(
          error?.response?.data?.message ||
            error?.message ||
            "Unable to load content planner.",
        );
      } finally {
        if (requestSequence !== requestSequenceRef.current) {
          return;
        }

        setInitialLoading(false);
        setTableLoading(false);
      }
    },
    [filters],
  );

  useEffect(() => {
    loadPlanner({
      initial: true,
      nextFilters: INITIAL_FILTERS,
    });
  }, [loadPlanner]);

  const updateSearch = useCallback((search) => {
    setFilters((prev) => ({
      ...prev,
      search,
    }));
  }, []);

  const updateOrganization = useCallback((organization) => {
    setFilters((prev) => ({
      ...prev,
      organization,
    }));
  }, []);

  return {
    planner,
    filters,

    initialLoading,
    tableLoading,
    error,

    updateSearch,
    updateOrganization,
    reload: loadPlanner,
  };
}
