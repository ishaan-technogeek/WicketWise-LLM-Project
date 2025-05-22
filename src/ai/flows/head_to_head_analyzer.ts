'use server';
/**
 * @fileOverview Generates a head-to-head summary between two players or teams.
 */

import { ai } from '@/ai/ai-instance';
import { z } from 'genkit';
import { getPlayerStats, getTeamStats, Player, Team } from '@/services/ipl';

const HeadToHeadInputSchema = z.object({
  entity1: z.string().describe('First player or team name'),
  entity2: z.string().describe('Second player or team name'),
  compareBy: z.enum(['Player vs Player', 'Team vs Team']).describe('Type of comparison'),
});
export type HeadToHeadInput = z.infer<typeof HeadToHeadInputSchema>;

const HeadToHeadOutputSchema = z.object({
  summary: z.string().describe('A head-to-head comparative summary of the two entities.'),
});
export type HeadToHeadOutput = z.infer<typeof HeadToHeadOutputSchema>;

export async function headToHeadAnalyzer(input: HeadToHeadInput): Promise<HeadToHeadOutput> {
  return headToHeadFlow(input);
}

const needsDisclaimerTool = ai.defineTool({
  name: 'needsDisclaimer',
  description: 'Determine whether a disclaimer is required for the given entities.',
  inputSchema: z.object({
    entity1: z.string(),
    entity2: z.string(),
  }),
  outputSchema: z.boolean(),
},
async ({ entity1, entity2 }) => {
  // Placeholder: always true for now
  return true;
});

const headToHeadPrompt = ai.definePrompt({
  name: 'headToHeadPrompt',
  input: {
    schema: z.object({
      entity1: z.string(),
      entity2: z.string(),
      compareBy: z.enum(['Player vs Player', 'Team vs Team']),
      stats1: z.string(),
      stats2: z.string(),
      needsDisclaimer: z.boolean(),
    })
  },
  output: {
    schema: z.object({
      summary: z.string(),
    })
  },
  prompt: `You are an expert IPL analyst. Provide a head-to-head comparison between {{{entity1}}} and {{{entity2}}} ({{{compareBy}}}) using the provided stats.

Stats for {{{entity1}}}: {{{stats1}}}

Stats for {{{entity2}}}: {{{stats2}}}

{{#if needsDisclaimer}}
Important Disclaimer: This analysis is AI-generated and for informational purposes only.
{{/if}}`,
  tools: [needsDisclaimerTool],
});

const headToHeadFlow = ai.defineFlow<
  typeof HeadToHeadInputSchema,
  typeof HeadToHeadOutputSchema
>({
  name: 'headToHeadFlow',
  inputSchema: HeadToHeadInputSchema,
  outputSchema: HeadToHeadOutputSchema,
},
async input => {
  let stats1: any, stats2: any;
  // Attempt to fetch stats for entity1
  try {
    if (input.compareBy === 'Player vs Player') {
      const p1: Player = { name: input.entity1, team: 'Unknown' };
      stats1 = await getPlayerStats(p1);
    } else {
      const t1: Team = { name: input.entity1, city: 'Unknown' };
      stats1 = await getTeamStats(t1);
    }
  } catch {
    throw new Error(`Could not fetch stats for ${input.entity1}`);
  }

  // Attempt to fetch stats for entity2
  try {
    if (input.compareBy === 'Player vs Player') {
      const p2: Player = { name: input.entity2, team: 'Unknown' };
      stats2 = await getPlayerStats(p2);
    } else {
      const t2: Team = { name: input.entity2, city: 'Unknown' };
      stats2 = await getTeamStats(t2);
    }
  } catch {
    throw new Error(`Could not fetch stats for ${input.entity2}`);
  }

  const { output } = await headToHeadPrompt({
    entity1: input.entity1,
    entity2: input.entity2,
    compareBy: input.compareBy,
    stats1: JSON.stringify(stats1),
    stats2: JSON.stringify(stats2),
    needsDisclaimer: await needsDisclaimerTool({ entity1: input.entity1, entity2: input.entity2 }),
  });

  return { summary: output!.summary };
});
