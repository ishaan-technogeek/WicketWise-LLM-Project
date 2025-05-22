"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardContext } from "@/contexts/dashboard-context";

export const PastQueries = () => {
  const { queries } = useDashboardContext();

  return (
    <Card>
      <CardHeader>
        <CardTitle>📜 Past Queries</CardTitle>
      </CardHeader>
      <CardContent>
        {queries.length === 0 ? (
          <p>No past queries yet.</p>
        ) : (
          <ul>
            {queries.map((query, index) => (
              <li key={index} className="mb-4">
                <p className="font-semibold">{query.query}</p>
                <p>{query.response}</p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
};
