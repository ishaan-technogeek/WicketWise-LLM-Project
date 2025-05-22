// app/components/WhatIfScenarios.tsx
'use client';

import { FormEvent, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDashboardContext } from '@/contexts/dashboard-context';
import { useToast } from '@/hooks/use-toast';
import { analyzeWhatIf } from '@/ai/flows/what_if_scenarios';

export const WhatIfScenarios = () => {
  const [messages, setMessages] = useState<{ sender: 'user' | 'ai'; text: string }[]>([]);
  const [currentScenario, setCurrentScenario] = useState('');
  const { addQuery } = useDashboardContext();
  const { toast } = useToast();

  const handleAskScenario = async (e?: FormEvent) => {
    e?.preventDefault();
    const scenario = currentScenario.trim();
    if (!scenario) return;

    // Add user message
    setMessages(msgs => [...msgs, { sender: 'user', text: scenario }]);

    try {
      const { summary } = await analyzeWhatIf({ scenario });
      // Add AI response
      setMessages(msgs => [...msgs, { sender: 'user', text: scenario }, { sender: 'ai', text: summary }]);
      // Save to history
      addQuery({ query: scenario, response: summary });
      toast({ title: 'Scenario Saved', description: 'Scenario saved to your history.' });
    } catch (err: any) {
      toast({ variant: 'destructive', title: 'Error', description: err.message });
    } finally {
      setCurrentScenario('');
    }
  };

  return (
    <Card className="space-y-4">
      <CardHeader>
        <CardTitle> What-If Scenarios</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="h-64 overflow-y-auto space-y-2">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`p-2 rounded-md ${
                message.sender === 'user'
                  ? 'bg-secondary text-secondary-foreground self-end'
                  : 'bg-muted text-muted-foreground self-start'
              }`}
            >
              {message.text}
            </div>
          ))}
        </div>

        <form className="flex space-x-2" onSubmit={handleAskScenario}>
          <Input
            placeholder="Enter your hypothetical scenario"
            value={currentScenario}
            onChange={e => setCurrentScenario(e.target.value)}
          />
          <Button type="submit">Ask WicketWise</Button>
        </form>

        <p className="text-xs text-muted-foreground mt-4">
          This is a hypothetical analysis based on past data and trends. It is not a prediction or guarantee of actual outcomes.
        </p>
      </CardContent>
    </Card>
  );
};
