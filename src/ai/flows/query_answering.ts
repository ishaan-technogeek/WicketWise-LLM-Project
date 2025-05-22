// app/ai/query_answering.ts
'use server';

import { z } from 'genkit';
import { ai } from '@/ai/ai-instance';

const QueryAnsweringInputSchema = z.object({
  query: z.string().describe('A free-form cricket data question.'),
});
export type QueryAnsweringInput = z.infer<typeof QueryAnsweringInputSchema>;

const QueryAnsweringOutputSchema = z.object({
  summary: z.string().describe('The answer or explanation from the LLM.'),
});
export type QueryAnsweringOutput = z.infer<typeof QueryAnsweringOutputSchema>;

// Tool to call your Python backend
const queryTool = ai.defineTool({
  name: 'queryTool',
  description: 'Send a natural-language query to the Python backend and get back a summary.',
  inputSchema: QueryAnsweringInputSchema,
  outputSchema: QueryAnsweringOutputSchema,
}, 
async ({ query }) => {
  const res = await fetch('http://127.0.0.1:8000/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    throw new Error(`Backend error: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();
  // Assuming your Python returns { summary: "...", needs_chart: boolean }
  return { summary: data.summary };
});

// A no-prompt wrapper flow: just invokes the tool
export const queryAnsweringFlow = ai.defineFlow<
  typeof QueryAnsweringInputSchema,
  typeof QueryAnsweringOutputSchema
>({
  name: 'queryAnsweringFlow',
  inputSchema: QueryAnsweringInputSchema,
  outputSchema: QueryAnsweringOutputSchema,
},
async input => {
  const result = await queryTool({ query: input.query });
  return { summary: result.summary };
});

export async function answerQuery(input: QueryAnsweringInput): Promise<QueryAnsweringOutput> {
  return queryAnsweringFlow(input);
}
