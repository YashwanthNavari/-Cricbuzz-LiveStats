# Database Readiness Analysis Report

This document evaluates whether the normalized 10-table cricket database schema is structurally sufficient to answer all 25 analytical SQL queries. For each query, we examine the required tables, columns, potential data gaps, and recommend schema improvements.

---

## Technical Audit of 25 SQL Queries

### Q1: Calculate the Points Table for a given Series
* **Required Tables:** `matches`, `teams`, `innings`
* **Required Columns:** `matches.series_id`, `matches.winner_id`, `matches.team1_id`, `matches.team2_id`, `innings.runs`, `innings.overs`, `innings.wickets`
* **Missing Columns / Data:** Net Run Rate (NRR) requires knowing if a team was bowled out. To calculate this accurately under ICC rules, the divisor overs must roll up to the maximum match limit (e.g., 20 or 50 overs) if a team is bowled out. The schema currently lacks the scheduled overs limit per match.
* **Recommendation:** Add `match_overs_limit` (Integer) to `matches` table to capture rain-curtailed match limits.

### Q2: Top 10 run-scorers in a tournament
* **Required Tables:** `batting_scores`, `players`, `innings`, `matches`
* **Required Columns:** `batting_scores.runs`, `batting_scores.balls`, `batting_scores.out`, `players.name`, `matches.series_id`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q3: Most wickets taken in a tournament
* **Required Tables:** `bowling_scores`, `players`, `innings`, `matches`
* **Required Columns:** `bowling_scores.wickets`, `bowling_scores.runs_conceded`, `players.name`, `matches.series_id`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q4: Highest strike rate for batsmen facing at least 100 balls
* **Required Tables:** `batting_scores`, `players`
* **Required Columns:** `batting_scores.runs`, `batting_scores.balls`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q5: Best economy rate for bowlers who bowled at least 15 overs
* **Required Tables:** `bowling_scores`, `players`
* **Required Columns:** `bowling_scores.overs`, `bowling_scores.runs_conceded`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q6: Toss impact on match wins
* **Required Tables:** `matches`
* **Required Columns:** `matches.toss_winner_id`, `matches.winner_id`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q7: Top 5 highest batting partnerships
* **Required Tables:** `partnerships`, `players`, `innings`, `matches`
* **Required Columns:** `partnerships.runs`, `partnerships.balls`, `players.name`, `matches.match_desc`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q8: Most catches by a fielder
* **Required Tables:** `fielding_records`, `players`
* **Required Columns:** `fielding_records.catches`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q9: Most stumpings by a keeper
* **Required Tables:** `fielding_records`, `players`
* **Required Columns:** `fielding_records.stumpings`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q10: Head-to-head records between two teams
* **Required Tables:** `matches`
* **Required Columns:** `matches.team1_id`, `matches.team2_id`, `matches.winner_id`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q11: Average runs scored per innings at each venue
* **Required Tables:** `innings`, `matches`, `venues`
* **Required Columns:** `innings.runs`, `matches.venue_id`, `venues.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q12: Win percentage of batting first vs chasing at each venue
* **Required Tables:** `matches`, `venues`
* **Required Columns:** `matches.venue_id`, `matches.toss_winner_id`, `matches.toss_decision`, `matches.winner_id`, `venues.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q13: Player with most "Man of the Match" (match winner) awards
* **Required Tables:** `matches`, `players`
* **Required Columns:** `matches.player_of_the_match_id`, `players.name`
* **Missing Columns / Data:** **Missing Column & Relationship**. The `matches` table currently lacks a foreign key link to track which player was awarded the Man of the Match.
* **Recommendation:** Add `player_of_the_match_id` (Integer, references `players.id`) to the `matches` table.

### Q14: Bowlers with most maiden overs
* **Required Tables:** `bowling_scores`, `players`
* **Required Columns:** `bowling_scores.maidens`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q15: Most sixes by a batsman
* **Required Tables:** `batting_scores`, `players`
* **Required Columns:** `batting_scores.sixes`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q16: Wicket-takers classified by dismissal types
* **Required Tables:** `batting_scores`
* **Required Columns:** `batting_scores.dismissal_type`, `batting_scores.out`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q17: Batsmen who remained not out the most times
* **Required Tables:** `batting_scores`, `players`
* **Required Columns:** `batting_scores.out`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q18: Rolling average of runs for a specific player over last 5 matches
* **Required Tables:** `batting_scores`, `innings`, `matches`
* **Required Columns:** `batting_scores.player_id`, `batting_scores.runs`, `matches.match_start_time`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q19: Standard deviation of scores for top 10 batsmen (consistency analysis)
* **Required Tables:** `batting_scores`, `players`
* **Required Columns:** `batting_scores.runs`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q20: Best bowling figures in a single match
* **Required Tables:** `bowling_scores`, `players`, `innings`, `matches`
* **Required Columns:** `bowling_scores.wickets`, `bowling_scores.runs_conceded`, `players.name`, `matches.match_desc`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q21: Most prolific batting pairs
* **Required Tables:** `partnerships`, `players`
* **Required Columns:** `partnerships.runs`, `partnerships.batsman1_id`, `partnerships.batsman2_id`, `players.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q22: Teams with highest boundaries ratio in a series
* **Required Tables:** `batting_scores`, `innings`, `matches`, `teams`
* **Required Columns:** `batting_scores.runs`, `batting_scores.fours`, `batting_scores.sixes`, `innings.batting_team_id`, `matches.series_id`, `teams.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q23: Ratio of extras conceded by team in an innings
* **Required Tables:** `innings`, `teams`
* **Required Columns:** `innings.runs`, `innings.bowling_team_id`, `teams.name`
* **Missing Columns / Data:** **Missing Columns**. The `innings` table stores total runs and wickets, but does not split out extra runs (wides, no-balls, leg-byes, byes) conceded.
* **Recommendation:** Add `extras`, `wides`, `no_balls`, `byes`, and `leg_byes` (all Integers) to the `innings` table.

### Q24: List of all live matches currently played
* **Required Tables:** `matches`, `series`, `teams`
* **Required Columns:** `matches.is_live`, `matches.status`, `series.name`, `teams.name`
* **Missing Columns / Data:** None.
* **Readiness:** **Ready**.

### Q25: Success rate of a team chasing targets of 150+ runs
* **Required Tables:** `innings`, `matches`, `teams`
* **Required Columns:** `innings.runs`, `innings.innings_num`, `innings.batting_team_id`, `matches.winner_id`, `teams.name`
* **Missing Columns / Data:** None (targets are derived as `1st innings runs + 1`).
* **Readiness:** **Ready**.

---

## Recommended Schema Improvements

To guarantee 100% database readiness and data integrity for all 25 queries, we recommend the following DDL updates:

1. **Award Tracking (Q13):**
   ```sql
   ALTER TABLE matches ADD COLUMN player_of_the_match_id INT REFERENCES players(id) ON DELETE SET NULL;
   ```
2. **Extras Aggregation (Q23):**
   ```sql
   ALTER TABLE innings 
   ADD COLUMN extras INT DEFAULT 0,
   ADD COLUMN wides INT DEFAULT 0,
   ADD COLUMN no_balls INT DEFAULT 0,
   ADD COLUMN byes INT DEFAULT 0,
   ADD COLUMN leg_byes INT DEFAULT 0;
   ```
3. **Over Limit Constraints (Q1 points table / NRR):**
   ```sql
   ALTER TABLE matches ADD COLUMN match_overs_limit INT DEFAULT 20; -- Default standard T20
   ```
4. **Composite Index for Head-to-Head (Q10):**
   ```sql
   CREATE INDEX idx_matches_head_to_head ON matches(team1_id, team2_id);
   ```
