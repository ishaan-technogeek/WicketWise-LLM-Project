// app/ai/what_if_scenarios.ts
'use server';

import { z } from 'genkit';
import { ai } from '@/ai/ai-instance';

const WhatIfInputSchema = z.object({
  scenario: z.string().describe('A hypothetical scenario, e.g. "If Virat Kohli played for CSK at Wankhede Stadium."'),
});
export type WhatIfInput = z.infer<typeof WhatIfInputSchema>;

const WhatIfOutputSchema = z.object({
  summary: z.string().describe('The LLM’s hypothetical analysis summary.'),
});
export type WhatIfOutput = z.infer<typeof WhatIfOutputSchema>;

// Tool that calls your FastAPI /whatif endpoint
const whatIfTool = ai.defineTool({
  name: 'whatIfTool',
  description: 'Send a hypothetical scenario to the Python backend and get back the LLM’s analysis.',
  inputSchema: WhatIfInputSchema,
  outputSchema: WhatIfOutputSchema,
},
async ({ scenario }) => {
  const res = await fetch('http://127.0.0.1:8000/what-if', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: scenario }),
  });
  if (!res.ok) {
    throw new Error(`Backend error: ${res.status} ${res.statusText}`);
  }
  const data = await res.json();
  // Assuming your Python route returns: { summary: "...", needs_chart: bool }
  return { summary: data.summary };
});

// Flow that just invokes the tool
export const whatIfFlow = ai.defineFlow<
  typeof WhatIfInputSchema,
  typeof WhatIfOutputSchema
>({
  name: 'whatIfFlow',
  inputSchema: WhatIfInputSchema,
  outputSchema: WhatIfOutputSchema,
},
async input => {
  const { summary } = await whatIfTool({ scenario: input.scenario });
  return { summary };
});

// Convenience wrapper
export async function analyzeWhatIf(input: WhatIfInput): Promise<WhatIfOutput> {
  return whatIfFlow(input);
}
