/**
 * Represents a player in the IPL.
 */
export interface Player {
  /**
   * The name of the player.
   */
  name: string;
  /**
   * The team the player plays for.
   */
  team: string;
}

/**
 * Represents a team in the IPL.
 */
export interface Team {
  /**
   * The name of the team.
   */
  name: string;
  /**
   * The city the team represents.
   */
  city: string;
}

/**
 * Represents IPL statistics for a player or team.
 */
export interface IplStats {
  /**
   * The number of matches played.
   */
  matchesPlayed: number;
  /**
   * The number of runs scored.
   */
  runsScored: number;
  /**
   * The number of wickets taken.
   */
  wicketsTaken: number;
  /**
   * The batting average.
   */
  battingAverage: number;
}

// ipl.ts
export async function getPlayerStats(player: Player): Promise<IplStats> {
  const response = await fetch('http://localhost:8000/summary', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: player.name})
  });
  return await response.json();
}

export async function getTeamStats(team: Team): Promise<IplStats> {
  const response = await fetch('http://localhost:8000/summary', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: team.name})
  });
  return await response.json();
}
