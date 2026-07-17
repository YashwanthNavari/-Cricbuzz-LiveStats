# Cricbuzz Database Analytics Queries Configuration
# Contains 25 SQL queries designed to be compatible with SQLite and PostgreSQL.

ANALYTICAL_QUERIES = {
    "Q1": {
        "title": "Calculate Points Table for a given Series",
        "sql": """
WITH match_results AS (
    SELECT 
        m.id AS match_id,
        m.series_id,
        t1.id AS team_id,
        t1.name AS team_name,
        CASE WHEN m.winner_id = t1.id THEN 1 ELSE 0 END AS win,
        CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != t1.id THEN 1 ELSE 0 END AS loss,
        CASE WHEN m.winner_id IS NULL AND m.is_completed = 1 THEN 1 ELSE 0 END AS nr,
        CASE WHEN m.winner_id = t1.id THEN 2 WHEN m.winner_id IS NULL AND m.is_completed = 1 THEN 1 ELSE 0 END AS points
    FROM matches m
    JOIN teams t1 ON m.team1_id = t1.id
    WHERE m.series_id = :series_id OR :series_id = -1
    UNION ALL
    SELECT 
        m.id AS match_id,
        m.series_id,
        t2.id AS team_id,
        t2.name AS team_name,
        CASE WHEN m.winner_id = t2.id THEN 1 ELSE 0 END AS win,
        CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != t2.id THEN 1 ELSE 0 END AS loss,
        CASE WHEN m.winner_id IS NULL AND m.is_completed = 1 THEN 1 ELSE 0 END AS nr,
        CASE WHEN m.winner_id = t2.id THEN 2 WHEN m.winner_id IS NULL AND m.is_completed = 1 THEN 1 ELSE 0 END AS points
    FROM matches m
    JOIN teams t2 ON m.team2_id = t2.id
    WHERE m.series_id = :series_id OR :series_id = -1
),
team_runs AS (
    SELECT 
        i.batting_team_id AS team_id,
        SUM(i.runs) AS total_runs_scored,
        SUM(
            CASE 
                WHEN i.wickets = 10 THEN COALESCE(m.match_overs_limit, 20)
                ELSE (CAST(i.overs AS INT) * 6 + (i.overs - CAST(i.overs AS INT)) * 10) / 6.0
            END
        ) AS total_overs_faced
    FROM innings i
    JOIN matches m ON i.match_id = m.id
    WHERE m.series_id = :series_id OR :series_id = -1
    GROUP BY i.batting_team_id
),
team_conceded AS (
    SELECT 
        i.bowling_team_id AS team_id,
        SUM(i.runs) AS total_runs_conceded,
        SUM(
            CASE 
                WHEN i.wickets = 10 THEN COALESCE(m.match_overs_limit, 20)
                ELSE (CAST(i.overs AS INT) * 6 + (i.overs - CAST(i.overs AS INT)) * 10) / 6.0
            END
        ) AS total_overs_bowled
    FROM innings i
    JOIN matches m ON i.match_id = m.id
    WHERE m.series_id = :series_id OR :series_id = -1
    GROUP BY i.bowling_team_id
)
SELECT 
    mr.team_name AS "Team",
    COUNT(DISTINCT mr.match_id) AS "Played",
    SUM(mr.win) AS "Wins",
    SUM(mr.loss) AS "Losses",
    SUM(mr.nr) AS "No Result",
    SUM(mr.points) AS "Points",
    ROUND(
        COALESCE(CAST(tr.total_runs_scored AS FLOAT) / NULLIF(tr.total_overs_faced, 0), 0) - 
        COALESCE(CAST(tc.total_runs_conceded AS FLOAT) / NULLIF(tc.total_overs_bowled, 0), 0), 3
    ) AS "Net Run Rate"
FROM match_results mr
LEFT JOIN team_runs tr ON mr.team_id = tr.team_id
LEFT JOIN team_conceded tc ON mr.team_id = tc.team_id
GROUP BY mr.team_id, mr.team_name, tr.total_runs_scored, tr.total_overs_faced, tc.total_runs_conceded, tc.total_overs_bowled
ORDER BY "Points" DESC, "Net Run Rate" DESC;
        """,
        "description": "Calculates points table statistics (Played, Wins, Losses, No-Results, Points, and Net Run Rate) for all teams playing in a series.",
        "params": {"series_id": "series"},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Team", "y": "Points", "color": "Team"},
    },
    "Q2": {
        "title": "Top 10 Run-Scorers in a Tournament (Series)",
        "sql": """
SELECT 
    p.name AS "Player Name",
    t.name AS "Team",
    SUM(bs.runs) AS "Total Runs",
    SUM(bs.balls) AS "Balls Faced",
    ROUND(CAST(SUM(bs.runs) AS FLOAT) * 100.0 / NULLIF(SUM(bs.balls), 0), 2) AS "Strike Rate",
    SUM(CASE WHEN bs.out = 0 THEN 1 ELSE 0 END) AS "Not Outs",
    MAX(bs.runs) AS "Highest Score"
FROM batting_scores bs
JOIN players p ON bs.player_id = p.id
JOIN innings i ON bs.innings_id = i.id
JOIN matches m ON i.match_id = m.id
JOIN teams t ON i.batting_team_id = t.id
WHERE m.series_id = :series_id OR :series_id = -1
GROUP BY p.id, p.name, t.id, t.name
ORDER BY "Total Runs" DESC
LIMIT 10;
        """,
        "description": "Identifies the top 10 batsmen based on total runs scored in a specific series or across all series, including high scores and strike rates.",
        "params": {"series_id": "series"},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Total Runs", "color": "Team"},
    },
    "Q3": {
        "title": "Most Wickets Taken in a Tournament (Series)",
        "sql": """
SELECT 
    p.name AS "Player Name",
    t.name AS "Team",
    SUM(bowl.wickets) AS "Wickets",
    SUM(bowl.runs_conceded) AS "Runs Conceded",
    ROUND(SUM(
        (CAST(bowl.overs AS INT) * 6 + (bowl.overs - CAST(bowl.overs AS INT)) * 10)
    ) / 6.0, 1) AS "Overs Bowled",
    ROUND(CAST(SUM(bowl.runs_conceded) AS FLOAT) / NULLIF(SUM(bowl.wickets), 0), 2) AS "Average",
    ROUND(CAST(SUM(bowl.runs_conceded) AS FLOAT) * 6.0 / NULLIF(SUM(
        (CAST(bowl.overs AS INT) * 6 + (bowl.overs - CAST(bowl.overs AS INT)) * 10)
    ), 0), 2) AS "Economy"
FROM bowling_scores bowl
JOIN players p ON bowl.player_id = p.id
JOIN innings i ON bowl.innings_id = i.id
JOIN matches m ON i.match_id = m.id
JOIN teams t ON i.bowling_team_id = t.id
WHERE m.series_id = :series_id OR :series_id = -1
GROUP BY p.id, p.name, t.id, t.name
ORDER BY "Wickets" DESC, "Economy" ASC
LIMIT 10;
        """,
        "description": "Lists top bowlers in a series ordered by total wickets taken, with bowling averages and economies.",
        "params": {"series_id": "series"},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Wickets", "color": "Team"},
    },
    "Q4": {
        "title": "Highest Strike Rate for Batsmen Facing at Least 100 Balls",
        "sql": """
SELECT 
    p.name AS "Player Name",
    SUM(bs.runs) AS "Total Runs",
    SUM(bs.balls) AS "Balls Faced",
    ROUND(CAST(SUM(bs.runs) AS FLOAT) * 100.0 / SUM(bs.balls), 2) AS "Strike Rate"
FROM batting_scores bs
JOIN players p ON bs.player_id = p.id
GROUP BY p.id, p.name
HAVING SUM(bs.balls) >= 100
ORDER BY "Strike Rate" DESC
LIMIT 15;
        """,
        "description": "Retrieves the batsmen with highest batting strike rates overall, filtering for a minimum of 100 balls faced to ensure statistical significance.",
        "params": {},
        "chart_type": "scatter",
        "chart_kwargs": {
            "x": "Balls Faced",
            "y": "Strike Rate",
            "text": "Player Name",
            "size": "Total Runs",
        },
    },
    "Q5": {
        "title": "Best Economy Rate for Bowlers who Bowled at least 15 Overs",
        "sql": """
SELECT 
    p.name AS "Player Name",
    ROUND(SUM(
        (CAST(bowl.overs AS INT) * 6 + (bowl.overs - CAST(bowl.overs AS INT)) * 10)
    ) / 6.0, 1) AS "Overs Bowled",
    SUM(bowl.runs_conceded) AS "Runs Conceded",
    SUM(bowl.wickets) AS "Wickets",
    ROUND(CAST(SUM(bowl.runs_conceded) AS FLOAT) * 6.0 / SUM(
        (CAST(bowl.overs AS INT) * 6 + (bowl.overs - CAST(bowl.overs AS INT)) * 10)
    ), 2) AS "Economy"
FROM bowling_scores bowl
JOIN players p ON bowl.player_id = p.id
GROUP BY p.id, p.name
HAVING SUM(
    (CAST(bowl.overs AS INT) * 6 + (bowl.overs - CAST(bowl.overs AS INT)) * 10)
) >= 90
ORDER BY "Economy" ASC
LIMIT 15;
        """,
        "description": "Finds the bowlers with the best economy rates, filtering for those who have bowled at least 15 overs (90 balls).",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Economy"},
    },
    "Q6": {
        "title": "Toss Impact on Match Outcomes",
        "sql": """
SELECT 
    CASE WHEN toss_winner_id = winner_id THEN 'Toss Winner Wins' ELSE 'Toss Winner Loses' END AS "Toss Outcome",
    COUNT(*) AS "Matches Count",
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM matches WHERE winner_id IS NOT NULL AND toss_winner_id IS NOT NULL), 2) AS "Win Percentage"
FROM matches
WHERE winner_id IS NOT NULL AND toss_winner_id IS NOT NULL
GROUP BY "Toss Outcome";
        """,
        "description": "Analyzes whether winning the toss has a statistical correlation with winning the match.",
        "params": {},
        "chart_type": "pie",
        "chart_kwargs": {"names": "Toss Outcome", "values": "Matches Count"},
    },
    "Q7": {
        "title": "Top 5 Highest Batting Partnerships",
        "sql": """
SELECT 
    p1.name AS "Batsman 1",
    p2.name AS "Batsman 2",
    t.name AS "Batting Team",
    pt.runs AS "Partnership Runs",
    pt.balls AS "Balls",
    pt.boundaries_fours AS "Fours",
    pt.boundaries_sixes AS "Sixes",
    CASE WHEN pt.unbroken = 1 THEN 'Unbroken' ELSE 'Broken' END AS "Status",
    m.match_desc AS "Match Details"
FROM partnerships pt
JOIN players p1 ON pt.batsman1_id = p1.id
JOIN players p2 ON pt.batsman2_id = p2.id
JOIN innings i ON pt.innings_id = i.id
JOIN matches m ON i.match_id = m.id
JOIN teams t ON i.batting_team_id = t.id
ORDER BY pt.runs DESC
LIMIT 5;
        """,
        "description": "Retrieves the top 5 largest partnerships (by runs scored) recorded in any match, showing the batsmen involved, team, and match.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {
            "x": "Partnership Runs",
            "y": "Match Details",
            "orientation": "h",
        },
    },
    "Q8": {
        "title": "Most Catches by a Fielder",
        "sql": """
SELECT 
    p.name AS "Player Name",
    SUM(fr.catches) AS "Catches",
    COUNT(DISTINCT i.match_id) AS "Matches"
FROM fielding_records fr
JOIN players p ON fr.player_id = p.id
JOIN innings i ON fr.innings_id = i.id
GROUP BY p.id, p.name
HAVING SUM(fr.catches) > 0
ORDER BY "Catches" DESC
LIMIT 10;
        """,
        "description": "Lists the players with the most catches taken in fielding positions.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Catches"},
    },
    "Q9": {
        "title": "Most Stumpings by a Wicket-Keeper",
        "sql": """
SELECT 
    p.name AS "Player Name",
    SUM(fr.stumpings) AS "Stumpings",
    COUNT(DISTINCT i.match_id) AS "Matches"
FROM fielding_records fr
JOIN players p ON fr.player_id = p.id
JOIN innings i ON fr.innings_id = i.id
GROUP BY p.id, p.name
HAVING SUM(fr.stumpings) > 0
ORDER BY "Stumpings" DESC
LIMIT 10;
        """,
        "description": "Finds the wicket-keepers with the highest number of stumpings recorded in the database.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Stumpings"},
    },
    "Q10": {
        "title": "Head-to-Head Records Between Two Teams",
        "sql": """
SELECT 
    t.name AS "Team Name",
    COUNT(*) AS "Played",
    SUM(CASE WHEN m.winner_id = t.id THEN 1 ELSE 0 END) AS "Wins",
    SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != t.id THEN 1 ELSE 0 END) AS "Losses",
    SUM(CASE WHEN m.winner_id IS NULL AND m.is_completed = 1 THEN 1 ELSE 0 END) AS "No Result",
    ROUND(SUM(CASE WHEN m.winner_id = t.id THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS "Win Ratio (%)"
FROM matches m
JOIN teams t ON t.id IN (m.team1_id, m.team2_id)
WHERE (m.team1_id = :team1_id AND m.team2_id = :team2_id)
   OR (m.team1_id = :team2_id AND m.team2_id = :team1_id)
GROUP BY t.id, t.name;
        """,
        "description": "Calculates the head-to-head match stats between two selected teams: matches played, wins, losses, draws, and win ratios.",
        "params": {"team1_id": "team", "team2_id": "team"},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Team Name", "y": "Wins", "color": "Team Name"},
    },
    "Q11": {
        "title": "Average Runs Scored Per Innings at Each Venue",
        "sql": """
SELECT 
    v.name AS "Venue Name",
    v.city AS "City",
    COUNT(DISTINCT i.id) AS "Innings Played",
    ROUND(AVG(i.runs), 2) AS "Average Runs",
    MAX(i.runs) AS "Highest Innings Score",
    MIN(i.runs) AS "Lowest Innings Score"
FROM innings i
JOIN matches m ON i.match_id = m.id
JOIN venues v ON m.venue_id = v.id
GROUP BY v.id, v.name, v.city
HAVING COUNT(DISTINCT i.id) >= 2
ORDER BY "Average Runs" DESC;
        """,
        "description": "Compares cricket venues based on average runs scored per innings, filtering for venues that hosted at least 2 innings.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Venue Name", "y": "Average Runs"},
    },
    "Q12": {
        "title": "Win Percentage of Batting First vs Chasing at Each Venue",
        "sql": """
WITH venue_stats AS (
    SELECT 
        v.id AS venue_id,
        v.name AS venue_name,
        m.id AS match_id,
        CASE 
            WHEN m.winner_id IS NULL THEN 'No Winner'
            WHEN m.winner_id = i.batting_team_id THEN 'Batting First Wins'
            ELSE 'Chasing Wins'
        END AS outcome
    FROM matches m
    JOIN venues v ON m.venue_id = v.id
    JOIN innings i ON i.match_id = m.id AND i.innings_num = 1
    WHERE m.winner_id IS NOT NULL
)
SELECT 
    venue_name AS "Venue Name",
    COUNT(DISTINCT match_id) AS "Total Matches",
    SUM(CASE WHEN outcome = 'Batting First Wins' THEN 1 ELSE 0 END) AS "Bat First Wins",
    SUM(CASE WHEN outcome = 'Chasing Wins' THEN 1 ELSE 0 END) AS "Chase Wins",
    ROUND(SUM(CASE WHEN outcome = 'Batting First Wins' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(DISTINCT match_id), 2) AS "Bat First Win %",
    ROUND(SUM(CASE WHEN outcome = 'Chasing Wins' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(DISTINCT match_id), 2) AS "Chase Win %"
FROM venue_stats
GROUP BY venue_id, venue_name
ORDER BY "Total Matches" DESC;
        """,
        "description": "Shows whether batting first or chasing holds an advantage at each venue hosting matches.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Venue Name", "y": "Bat First Win %"},
    },
    "Q13": {
        "title": "Players with Most 'Player of the Match' Awards",
        "sql": """
SELECT 
    p.name AS "Player Name",
    p.role AS "Role",
    COUNT(m.id) AS "Awards Count"
FROM matches m
JOIN players p ON m.player_of_the_match_id = p.id
GROUP BY p.id, p.name, p.role
ORDER BY "Awards Count" DESC, p.name ASC
LIMIT 10;
        """,
        "description": "Identifies the top players who have been awarded the Man/Player of the Match award.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Awards Count"},
    },
    "Q14": {
        "title": "Bowlers with Most Maiden Overs",
        "sql": """
SELECT 
    p.name AS "Player Name",
    SUM(bowl.maidens) AS "Maidens",
    ROUND(SUM(
        (CAST(bowl.overs AS INT) * 6 + (bowl.overs - CAST(bowl.overs AS INT)) * 10)
    ) / 6.0, 1) AS "Overs Bowled",
    SUM(bowl.wickets) AS "Wickets"
FROM bowling_scores bowl
JOIN players p ON bowl.player_id = p.id
GROUP BY p.id, p.name
HAVING SUM(bowl.maidens) > 0
ORDER BY "Maidens" DESC, "Wickets" DESC
LIMIT 10;
        """,
        "description": "Lists bowlers who have bowled the highest number of maiden overs (overs with zero runs conceded).",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Maidens"},
    },
    "Q15": {
        "title": "Most Sixes hit by a Batsman",
        "sql": """
SELECT 
    p.name AS "Player Name",
    SUM(bs.sixes) AS "Sixes",
    SUM(bs.fours) AS "Fours",
    SUM(bs.runs) AS "Runs"
FROM batting_scores bs
JOIN players p ON bs.player_id = p.id
GROUP BY p.id, p.name
HAVING SUM(bs.sixes) > 0
ORDER BY "Sixes" DESC, "Runs" DESC
LIMIT 15;
        """,
        "description": "Returns the list of players who have hit the highest number of sixes.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Sixes"},
    },
    "Q16": {
        "title": "Wicket-Takers Classified by Dismissal Types",
        "sql": """
SELECT 
    COALESCE(bs.dismissal_type, 'Not Out/Other') AS "Dismissal Type",
    COUNT(*) AS "Wickets Count",
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM batting_scores WHERE out = 1 AND dismissal_type IS NOT NULL), 2) AS "Percentage"
FROM batting_scores bs
WHERE bs.out = 1 AND bs.dismissal_type IS NOT NULL
GROUP BY bs.dismissal_type
ORDER BY "Wickets Count" DESC;
        """,
        "description": "Aggregates and breaks down how wickets are falling across the tournament (caught, bowled, lbw, run out, stumped, etc.).",
        "params": {},
        "chart_type": "pie",
        "chart_kwargs": {"names": "Dismissal Type", "values": "Wickets Count"},
    },
    "Q17": {
        "title": "Batsmen who Remained Not Out the Most Times",
        "sql": """
SELECT 
    p.name AS "Player Name",
    COUNT(*) AS "Innings Battted",
    SUM(CASE WHEN bs.out = 0 THEN 1 ELSE 0 END) AS "Not Outs",
    ROUND(SUM(CASE WHEN bs.out = 0 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) AS "Not Out Rate (%)"
FROM batting_scores bs
JOIN players p ON bs.player_id = p.id
GROUP BY p.id, p.name
HAVING SUM(CASE WHEN bs.out = 0 THEN 1 ELSE 0 END) > 0
ORDER BY "Not Outs" DESC, "Innings Battted" ASC
LIMIT 10;
        """,
        "description": "Lists the batsmen who have finished their innings without being dismissed the most times.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Not Outs"},
    },
    "Q18": {
        "title": "Rolling Average of Runs for a Specific Player over Last 5 Matches",
        "sql": """
SELECT 
    p.name AS "Player Name",
    m.match_desc AS "Match",
    m.match_start_time AS "Date",
    bs.runs AS "Runs Scored",
    ROUND(AVG(bs.runs) OVER (
        PARTITION BY bs.player_id 
        ORDER BY m.match_start_time 
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ), 2) AS "Rolling Avg (5 Matches)"
FROM batting_scores bs
JOIN players p ON bs.player_id = p.id
JOIN innings i ON bs.innings_id = i.id
JOIN matches m ON i.match_id = m.id
WHERE bs.player_id = :player_id
ORDER BY m.match_start_time ASC;
        """,
        "description": "Plots the performance trend (rolling average over a 5-match window) for a single batsman over time.",
        "params": {"player_id": "player"},
        "chart_type": "line",
        "chart_kwargs": {"x": "Date", "y": "Rolling Avg (5 Matches)", "text": "Match"},
    },
    "Q19": {
        "title": "Standard Deviation of Scores for Top 10 Batsmen",
        "sql": """
WITH top_batsmen AS (
    SELECT player_id
    FROM batting_scores
    GROUP BY player_id
    HAVING SUM(runs) >= 150
)
SELECT 
    p.name AS "Player Name",
    COUNT(bs.id) AS "Innings Battted",
    SUM(bs.runs) AS "Total Runs",
    ROUND(AVG(bs.runs), 2) AS "Average",
    ROUND(
        CAST(
            (SUM(bs.runs * bs.runs) - (SUM(bs.runs) * SUM(bs.runs)) / CAST(COUNT(bs.id) AS FLOAT)) 
            / NULLIF(COUNT(bs.id) - 1, 0)
        AS FLOAT)
    , 2) AS "Variance Indicator"
FROM batting_scores bs
JOIN players p ON bs.player_id = p.id
WHERE bs.player_id IN (SELECT player_id FROM top_batsmen)
GROUP BY p.id, p.name
HAVING COUNT(bs.id) >= 3
ORDER BY "Total Runs" DESC
LIMIT 10;
        """,
        "description": "Evaluates consistency of top batsmen (with minimum 150 total runs and 3 innings bat) by analyzing variance indicator (variance proxy). Lower indicates high consistency.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Variance Indicator"},
    },
    "Q20": {
        "title": "Best Bowling Figures in a Single Match",
        "sql": """
SELECT 
    p.name AS "Player Name",
    bowl.wickets AS "Wickets",
    bowl.runs_conceded AS "Runs Conceded",
    bowl.overs AS "Overs",
    bowl.economy AS "Economy",
    m.match_desc AS "Match",
    t.name AS "Team"
FROM bowling_scores bowl
JOIN players p ON bowl.player_id = p.id
JOIN innings i ON bowl.innings_id = i.id
JOIN matches m ON i.match_id = m.id
JOIN teams t ON i.bowling_team_id = t.id
ORDER BY bowl.wickets DESC, bowl.runs_conceded ASC
LIMIT 10;
        """,
        "description": "Displays the top 10 best bowling spells in a single match, prioritized by highest wickets and fewest runs conceded.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Player Name", "y": "Wickets", "color": "Runs Conceded"},
    },
    "Q21": {
        "title": "Most Prolific Batting Pairs (Partnerships)",
        "sql": """
SELECT 
    p1.name AS "Batsman 1",
    p2.name AS "Batsman 2",
    SUM(pt.runs) AS "Total Runs",
    SUM(pt.balls) AS "Total Balls",
    COUNT(*) AS "Innings Together",
    ROUND(CAST(SUM(pt.runs) AS FLOAT) * 100.0 / NULLIF(SUM(pt.balls), 0), 2) AS "Strike Rate"
FROM partnerships pt
JOIN players p1 ON pt.batsman1_id = p1.id
JOIN players p2 ON pt.batsman2_id = p2.id
GROUP BY pt.batsman1_id, pt.batsman2_id, p1.name, p2.name
ORDER BY "Total Runs" DESC
LIMIT 10;
        """,
        "description": "Aggregates partnership runs scored by pairs of batsmen who bat together frequently to identify highly productive duos.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {
            "x": "Total Runs",
            "y": "Batsman 1",
            "color": "Batsman 2",
            "orientation": "h",
        },
    },
    "Q22": {
        "title": "Teams with Highest Boundaries Ratio in a Series",
        "sql": """
SELECT 
    t.name AS "Team Name",
    SUM(bs.runs) AS "Total Batting Runs",
    SUM(bs.fours * 4 + bs.sixes * 6) AS "Boundary Runs",
    ROUND(SUM(bs.fours * 4 + bs.sixes * 6) * 100.0 / NULLIF(SUM(runs), 0), 2) AS "Boundary Ratio (%)"
FROM batting_scores bs
JOIN innings i ON bs.innings_id = i.id
JOIN matches m ON i.match_id = m.id
JOIN teams t ON i.batting_team_id = t.id
WHERE m.series_id = :series_id OR :series_id = -1
GROUP BY t.id, t.name
ORDER BY "Boundary Ratio (%)" DESC;
        """,
        "description": "Computes what percentage of a team's runs are scored purely through boundaries (fours and sixes) in a series.",
        "params": {"series_id": "series"},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Team Name", "y": "Boundary Ratio (%)"},
    },
    "Q23": {
        "title": "Ratio of Extras Conceded by Team in an Innings",
        "sql": """
SELECT 
    m.match_desc AS "Match",
    i.innings_num AS "Innings Num",
    t_bowl.name AS "Bowling Team",
    t_bat.name AS "Batting Team",
    i.runs AS "Total Score",
    i.extras AS "Extras",
    ROUND(CAST(i.extras AS FLOAT) * 100.0 / NULLIF(i.runs, 0), 2) AS "Extras Ratio (%)",
    i.wides AS "Wides",
    i.no_balls AS "No Balls",
    i.byes AS "Byes",
    i.leg_byes AS "Leg Byes"
FROM innings i
JOIN matches m ON i.match_id = m.id
JOIN teams t_bowl ON i.bowling_team_id = t_bowl.id
JOIN teams t_bat ON i.batting_team_id = t_bat.id
WHERE i.runs > 0
ORDER BY "Extras Ratio (%)" DESC
LIMIT 15;
        """,
        "description": "Analyzes discipline in bowling by calculating the ratio of extras (wides, no-balls, leg-byes, byes) to total runs conceded per innings.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {
            "x": "Extras Ratio (%)",
            "y": "Match",
            "color": "Bowling Team",
            "orientation": "h",
        },
    },
    "Q24": {
        "title": "List of All Live Matches Currently Active",
        "sql": """
SELECT 
    m.id AS "Match ID",
    s.name AS "Series",
    t1.name AS "Team 1",
    t2.name AS "Team 2",
    m.match_desc AS "Description",
    m.status AS "Current Status",
    m.match_start_time AS "Start Time"
FROM matches m
JOIN series s ON m.series_id = s.id
JOIN teams t1 ON m.team1_id = t1.id
JOIN teams t2 ON m.team2_id = t2.id
WHERE m.is_live = 1 OR m.is_live = 'true';
        """,
        "description": "Lists all matches flagged as live in the database, showing real-time status and teams involved.",
        "params": {},
        "chart_type": "table",
        "chart_kwargs": {},
    },
    "Q25": {
        "title": "Success Rate of a Team Chasing Targets of 150+ Runs",
        "sql": """
WITH chasing_runs AS (
    SELECT 
        m.id AS match_id,
        m.winner_id,
        i1.batting_team_id AS first_bat_team_id,
        i1.runs AS first_innings_runs,
        (i1.runs + 1) AS target,
        i2.batting_team_id AS chasing_team_id,
        i2.runs AS chase_runs
    FROM matches m
    JOIN innings i1 ON i1.match_id = m.id AND i1.innings_num = 1
    JOIN innings i2 ON i2.match_id = m.id AND i2.innings_num = 2
    WHERE i1.runs >= 149
),
chase_results AS (
    SELECT 
        chasing_team_id AS team_id,
        COUNT(*) AS total_chases,
        SUM(CASE WHEN winner_id = chasing_team_id THEN 1 ELSE 0 END) AS wins
    FROM chasing_runs
    GROUP BY chasing_team_id
)
SELECT 
    t.name AS "Team Name",
    cr.total_chases AS "Chases (150+)",
    cr.wins AS "Wins",
    (cr.total_chases - cr.wins) AS "Losses",
    ROUND(CAST(cr.wins AS FLOAT) * 100.0 / cr.total_chases, 2) AS "Chase Success Rate (%)"
FROM chase_results cr
JOIN teams t ON cr.team_id = t.id
ORDER BY "Chase Success Rate (%)" DESC;
        """,
        "description": "Calculates the win percentage for teams when chasing a score target of 150 or more in completed matches.",
        "params": {},
        "chart_type": "bar",
        "chart_kwargs": {"x": "Team Name", "y": "Chase Success Rate (%)"},
    },
}
