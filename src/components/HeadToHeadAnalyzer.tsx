'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { useDashboardContext } from '@/contexts/dashboard-context';
import { headToHeadAnalyzer } from '@/ai/flows/head_to_head_analyzer';

export const HeadToHeadAnalyzer = () => {
  const [compareBy, setCompareBy] = useState<'Player vs Player' | 'Team vs Team'>('Player vs Player');
  const [entity1, setEntity1] = useState('');
  const [entity2, setEntity2] = useState('');
  const [summary, setSummary] = useState<string | null>(null);
  const { toast } = useToast();
  const { addInsight } = useDashboardContext();

  const handleCompareEntities = async () => {
    if (!entity1 || !entity2) {
      toast({ variant: 'destructive', title: 'Error', description: 'Please enter both entities.' });
      return;
    }

    try {
      const { summary } = await headToHeadAnalyzer({ entity1, entity2, compareBy });
      setSummary(summary);
    } catch (e: any) {
      toast({ variant: 'destructive', title: 'Error', description: e.message });
    }
  };

  const handleSaveComparison = () => {
    if (summary) {
      addInsight({
        type: 'comparison',
        query: `Comparison between ${entity1} and ${entity2}`,
        result: summary,
      });
      toast({ title: 'Comparison Saved', description: 'Comparison saved to your history.' });
    } else {
      toast({ variant: 'destructive', title: 'Error', description: 'No comparison to save.' });
    }
  };

  return (
    <Card className="space-y-4">
      <CardHeader>
        <CardTitle>⚔️ Head-to-Head Analyzer</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Select onValueChange={(value) => setCompareBy(value as 'Player vs Player' | 'Team vs Team')} defaultValue={compareBy}>
          <SelectTrigger>
            <SelectValue placeholder="Compare by:" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Player vs Player">Player vs Player</SelectItem>
            <SelectItem value="Team vs Team">Team vs Team</SelectItem>
          </SelectContent>
        </Select>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Entity 1</label>
            <input
              type="text"
              placeholder="Enter Entity 1"
              value={entity1}
              onChange={(e) => setEntity1(e.target.value)}
              className="w-full rounded-md border px-3 py-2 placeholder:text-muted-foreground focus:outline-none focus:ring-2 bg-white"

            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Entity 2</label>
            <input
              type="text"
              placeholder="Enter Entity 2"
              value={entity2}
              onChange={(e) => setEntity2(e.target.value)}
              className="w-full rounded-md border px-3 py-2 placeholder:text-muted-foreground focus:outline-none focus:ring-2 bg-white"

            />
          </div>
        </div>

        <Button onClick={handleCompareEntities}>Compare Entities</Button>

        {summary && (
          <div className="mt-4 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Comparison Result</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{summary}</p>
              </CardContent>
            </Card>
            <Button variant="secondary" onClick={handleSaveComparison}>
              Save Comparison
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
