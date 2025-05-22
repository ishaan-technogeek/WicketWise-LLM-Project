"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export const AboutUs = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>ℹ️ About Us</CardTitle>
        <CardDescription>Learn more about WicketWise and our mission.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>
          WicketWise is your personal AI-powered IPL data insights agent. We provide in-depth statistical summaries,
          head-to-head comparisons, factual query answering, and what-if scenario analysis.
        </p>
        <p>Our mission is to make IPL data accessible and understandable for everyone.</p>
      </CardContent>
    </Card>
  );
};
