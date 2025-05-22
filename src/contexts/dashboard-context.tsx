"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

type Insight = {
  type: string;
  query: string;
  result: string;
};

type Query = {
  query: string;
  response: string;
};

type DashboardContextType = {
  insights: Insight[];
  queries: Query[];
  addInsight: (insight: Insight) => void;
  addQuery: (query: Query) => void;
};

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

const INSIGHTS_STORAGE_KEY = 'wicketwise_insights';
const QUERIES_STORAGE_KEY = 'wicketwise_queries';

export const DashboardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [insights, setInsights] = useState<Insight[]>(() => {
    if (typeof window !== 'undefined') {
      const storedInsights = localStorage.getItem(INSIGHTS_STORAGE_KEY);
      return storedInsights ? JSON.parse(storedInsights) : [];
    }
    return [];
  });
  const [queries, setQueries] = useState<Query[]>(() => {
    if (typeof window !== 'undefined') {
      const storedQueries = localStorage.getItem(QUERIES_STORAGE_KEY);
      return storedQueries ? JSON.parse(storedQueries) : [];
    }
    return [];
  });

  useEffect(() => {
    localStorage.setItem(INSIGHTS_STORAGE_KEY, JSON.stringify(insights));
  }, [insights]);

  useEffect(() => {
    localStorage.setItem(QUERIES_STORAGE_KEY, JSON.stringify(queries));
  }, [queries]);

  const addInsight = (insight: Insight) => {
    setInsights(prevInsights => [...prevInsights, insight]);
  };

  const addQuery = (query: Query) => {
    setQueries(prevQueries => [...prevQueries, query]);
  };

  const value: DashboardContextType = {
    insights,
    queries,
    addInsight,
    addQuery,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

export const useDashboardContext = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboardContext must be used within a DashboardProvider");
  }
  return context;
};
