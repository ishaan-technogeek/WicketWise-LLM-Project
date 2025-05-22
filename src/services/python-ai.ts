export async function answerQueryFromPython(query: string): Promise<string> {
  const response = await fetch('http://localhost:5000/answer', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({query}),
  });

  if (!response.ok) {
    throw new Error('Failed to get answer from Python backend');
  }

  const data = await response.json();
  return data.answer;
}