'use server';
/**
 * @fileOverview Generates a statistical summary about a player or team.
 *
 * - generateSummary - A function that generates a statistical summary about a player or team.
 * - GenerateSummaryInput - The input type for the generateSummary function.
 * - GenerateSummaryOutput - The return type for the generateSummary function.
 */

import {ai} from '@/ai/ai-instance';
import {z} from 'genkit';
import {getPlayerStats, getTeamStats, Player, Team} from '@/services/ipl';

const GenerateSummaryInputSchema = z.object({
  entityName: z.string().describe('The name of the player or team to summarize.'),
});
export type GenerateSummaryInput = z.infer<typeof GenerateSummaryInputSchema>;

const GenerateSummaryOutputSchema = z.object({
  summary: z.string().describe('A statistical summary of the player or team.'),
});
export type GenerateSummaryOutput = z.infer<typeof GenerateSummaryOutputSchema>;

export async function generateSummary(input: GenerateSummaryInput): Promise<GenerateSummaryOutput> {
  return generateSummaryFlow(input);
}

const needsDisclaimerTool = ai.defineTool({
  name: 'needsDisclaimer',
  description: 'Determine whether a disclaimer is required for the given entity name.',
  inputSchema: z.object({
    entityName: z.string().describe('The name of the player or team.'),
  }),
  outputSchema: z.boolean(),
},
async input => {
  // For now, always return true.  In a real application, you might check
  // a database or external source to determine if the entity requires a disclaimer.
  return true;
});


const generateSummaryPrompt = ai.definePrompt({
  name: 'generateSummaryPrompt',
  input: {
    schema: z.object({
      entityName: z.string().describe('The name of the player or team to summarize.'),
      entityType: z.enum(['player', 'team']).describe('The type of entity being summarized.'),
      stats: z.string().describe('Statistics for the player or team.'),
      needsDisclaimer: z.boolean().describe('Whether a disclaimer is needed'),
    }),
  },
  output: {
    schema: z.object({
      summary: z.string().describe('A statistical summary of the player or team.'),
    }),
  },
  prompt: `You are an expert IPL analyst. Generate a statistical summary of the following {{{entityType}}}, using the provided stats.

Statistics: {{{stats}}}

Entity Name: {{{entityName}}}


{{#if needsDisclaimer}}
Important Disclaimer: This analysis is AI-generated and for informational purposes only.
{{/if}}
`,
  tools: [needsDisclaimerTool]
});

const generateSummaryFlow = ai.defineFlow<
  typeof GenerateSummaryInputSchema,
  typeof GenerateSummaryOutputSchema
>({
  name: 'generateSummaryFlow',
  inputSchema: GenerateSummaryInputSchema,
  outputSchema: GenerateSummaryOutputSchema,
},
async input => {
  let player: Player | null = null;
  let team: Team | null = null;
  try {
    // Attempt to fetch player stats
    player = {name: input.entityName, team: 'Unknown'};
    await getPlayerStats(player);
    const {output} = await generateSummaryPrompt({
      entityName: input.entityName,
      entityType: 'player',
      stats: JSON.stringify(await getPlayerStats(player)),
      needsDisclaimer: await needsDisclaimerTool({entityName: input.entityName}),
    });
    return {summary: output!.summary};
  } catch (e) {
    // If player fetch fails, attempt to fetch team stats
    try {
      team = {name: input.entityName, city: 'Unknown'};
      await getTeamStats(team);
      const {output} = await generateSummaryPrompt({
        entityName: input.entityName,
        entityType: 'team',
        stats: JSON.stringify(await getTeamStats(team)),
        needsDisclaimer: await needsDisclaimerTool({entityName: input.entityName}),
      });
      return {summary: output!.summary};
    } catch (e) {
      // If both fail, throw an error
      throw new Error(`Could not find player or team with name ${input.entityName}`);
    }
  }
});
