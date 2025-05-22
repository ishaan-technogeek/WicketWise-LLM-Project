// app/components/QueryAnswering.tsx
'use client';

import { FormEvent, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDashboardContext } from '@/contexts/dashboard-context';
import { useToast } from '@/hooks/use-toast';

import { answerQuery } from '@/ai/flows/query_answering';

export const QueryAnswering = () => {
  const [messages, setMessages] = useState<{ sender: 'user' | 'ai'; text: string }[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const { addQuery } = useDashboardContext();
  const { toast } = useToast();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const q = currentQuery.trim();
    if (!q) return;

    // Show user message
    setMessages(msgs => [...msgs, { sender: 'user', text: q }]);

    try {
      const { summary } = await answerQuery({ query: q });
      // Show AI response
      setMessages(msgs => [...msgs, { sender: 'ai', text: summary }]);
      addQuery({ query: q, response: summary });
    } catch (err: any) {
      toast({ variant: 'destructive', title: 'Error', description: err.message });
    } finally {
      setCurrentQuery('');
    }
  };

  return (
    <Card className="space-y-4">
      <CardHeader>
        <CardTitle>💬 Query Answering</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="h-64 overflow-y-auto space-y-2">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`p-2 rounded-md ${
                msg.sender === 'user'
                  ? 'bg-secondary text-secondary-foreground self-end'
                  : 'bg-muted text-muted-foreground self-start'
              }`}
            >
              {msg.text}
            </div>
          ))}
        </div>
        <form className="flex space-x-2" onSubmit={handleSubmit}>
          <Input
            placeholder="Ask a cricket question..."
            value={currentQuery}
            onChange={e => setCurrentQuery(e.target.value)}
          />
          <Button type="submit">Ask</Button>
        </form>
      </CardContent>
    </Card>
  );
};
