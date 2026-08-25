import { useEffect, useState } from "react";

import insightsService from "../../services/insights.service";
import InsightsHeader from "../../components/insights/InsightsHeader";
import InsightsStats from "../../components/insights/InsightsStats";
import InsightsLayout from "../../components/insights/InsightsLayout";
import InsightsChartsLayout from "../../components/insights/InsightsChartsLayout";
import ReachChartCard from "../../components/insights/ReachChartCard";
import PlatformMixCard from "../../components/insights/PlatformMixCard";
import BestTimeCard from "../../components/insights/BestTimeCard";
import EngagementTypeCard from "../../components/insights/EngagementTypeCard";
import AccountPerformanceCard from "../../components/insights/AccountPerformanceCard";
export default function Insights() {
  const [insights, setInsights] = useState(null);
  const [filters, setFilters] = useState({
    organization: "all",
    period: "30D",
  });
  function handleOrganizationChange(organization) {
    setFilters((prev) => ({
      ...prev,
      organization,
    }));
  }

  function handlePeriodChange(period) {
    setFilters((prev) => ({
      ...prev,
      period,
    }));
  }

  useEffect(() => {
    loadInsights();
  }, []);

  async function loadInsights() {
    const response = await insightsService.getInsights();

    setInsights(response);
  }

  if (!insights) {
    return null;
  }

  return (
    <>
      <InsightsHeader
        filters={filters}
        onOrganizationChange={handleOrganizationChange}
        onPeriodChange={handlePeriodChange}
        onExport={() => console.log("Export")}
      />

      <InsightsLayout
        statistics={<InsightsStats statistics={insights.statistics} />}
        charts={
          <InsightsChartsLayout
            reachChart={<ReachChartCard data={insights.reach_chart} />}
            platformMix={<PlatformMixCard data={insights.platform_mix} />}
            bestTime={<BestTimeCard data={insights.best_time} />}
            engagementType={
              <EngagementTypeCard data={insights.engagement_types} />
            }
          />
        }
        performance={<AccountPerformanceCard accounts={insights.accounts} />}
      />
    </>
  );
}
