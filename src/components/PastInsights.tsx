"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardContext } from "@/contexts/dashboard-context";
import { IplStats } from "@/services/ipl";

const StatCard = ({ title, stats }: { title: string; stats: IplStats }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p>Matches Played: {stats.matchesPlayed}</p>
        <p>Runs Scored: {stats.runsScored}</p>
        <p>Wickets Taken: {stats.wicketsTaken}</p>
        <p>Batting Average: {stats.battingAverage}</p>
      </CardContent>
    </Card>
  );
};

export const PastInsights = () => {
  const { insights } = useDashboardContext();

  return (
    <Card>
      <CardHeader>
        <CardTitle>📁 Past Insights</CardTitle>
      </CardHeader>
      <CardContent>
        {insights.length === 0 ? (
          <p>No saved insights yet.</p>
        ) : (
          <ul>
            {insights.map((insight, index) => {
              if (insight.type === "comparison") {
                try {
                  const { entity1, entity2, stats1, stats2 } = JSON.parse(insight.result);
                  return (
                    <li key={index} className="mb-4">
                      <p className="font-semibold">{insight.query}</p>
                      <div className="grid grid-cols-2 gap-4 mt-4">
                        <StatCard title={`${entity1} Stats`} stats={stats1} />
                        <StatCard title={`${entity2} Stats`} stats={stats2} />
                      </div>
                    </li>
                  );
                } catch (e) {
                  return (
                    <li key={index} className="mb-4">
                      <p className="font-semibold">{insight.query}</p>
                      <p>Error rendering comparison.</p>
                      <p>{insight.result}</p>
                    </li>
                  );
                }
              } else {
                return (
                  <li key={index} className="mb-4">
                    <p className="font-semibold">{insight.query}</p>
                    <p>{insight.result}</p>
                  </li>
                );
              }
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
};

