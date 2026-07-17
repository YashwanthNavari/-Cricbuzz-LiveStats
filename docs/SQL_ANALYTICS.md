# SQL Analytics Documentation

This document catalogs the **25 complex analytical SQL queries** integrated into the Cricbuzz LiveStats platform. All queries are fully compatible with both **SQLite** (local development) and **PostgreSQL** (production deployment).

---

## Query Classification

To provide a structured user experience, queries are organized into three primary modules within the dashboard:

| Category | Query IDs | Key Metrics |
| --- | --- | --- |
| **League Standings & Venues** | Q1, Q6, Q10, Q11, Q12, Q24, Q25 | Points tables, Net Run Rates (NRR), toss correlations, venue scoring averages, chasing win ratios. |
| **Batting Analytics** | Q2, Q4, Q7, Q15, Q17, Q18, Q19, Q22 | Top run-scorers, high-density partnerships, strike rates, sixes, not outs, consistency (variance), boundaries ratios. |
| **Bowling, Fielding & Extras** | Q3, Q5, Q8, Q9, Q13, Q14, Q16, Q20, Q21, Q23 | Wickets, economies, catches, stumpings, maidens, dismissal categories, best figures, extras ratios. |

---

## Technical Highlights

### 1. Net Run Rate Calculation (Q1)
NRR calculation is implemented via the ICC standard:
$$\text{NRR} = \frac{\text{Total Runs Scored}}{\text{Total Overs Faced}} - \frac{\text{Total Runs Conceded}}{\text{Total Overs Bowled}}$$
If a team is bowled out (10 wickets down) before completing their allocated overs, the formula dynamically overrides their overs faced to the maximum match limit (`match_overs_limit` - usually 20 or 50):
```sql
CASE WHEN i.wickets = 10 THEN COALESCE(m.match_overs_limit, 20) ELSE ... END
```

### 2. Head-to-Head Records (Q10)
Uses standard set operations and parameterized bindings to calculate team-level metrics:
```sql
SELECT 
    t.name AS "Team Name",
    COUNT(*) AS "Played",
    SUM(CASE WHEN m.winner_id = t.id THEN 1 ELSE 0 END) AS "Wins",
    SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != t.id THEN 1 ELSE 0 END) AS "Losses"
FROM matches m
JOIN teams t ON t.id IN (m.team1_id, m.team2_id)
WHERE (m.team1_id = :team1_id AND m.team2_id = :team2_id)
   OR (m.team1_id = :team2_id AND m.team2_id = :team1_id)
GROUP BY t.id, t.name;
```

### 3. Window Aggregations (Q18)
Computes a rolling average of runs scored for a selected batsman over a 5-match window using SQL window functions:
```sql
SELECT 
    p.name AS "Player Name",
    bs.runs AS "Runs Scored",
    ROUND(AVG(bs.runs) OVER (
        PARTITION BY bs.player_id 
        ORDER BY m.match_start_time 
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ), 2) AS "Rolling Avg (5 Matches)"
...
```

### 4. Variance Indicator (Q19)
Computes a mathematical indicator of score consistency (as a proxy for standard deviation) compatible with standard SQL limits:
```sql
ROUND(
    CAST(
        (SUM(bs.runs * bs.runs) - (SUM(bs.runs) * SUM(bs.runs)) / CAST(COUNT(bs.id) AS FLOAT)) 
        / NULLIF(COUNT(bs.id) - 1, 0)
    AS FLOAT)
, 2) AS "Variance Indicator"
```
A lower variance indicates a highly consistent batsman.
