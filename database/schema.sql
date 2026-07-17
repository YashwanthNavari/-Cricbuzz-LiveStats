-- Normalized PostgreSQL Database Schema for Cricket Analytics

-- 1. Series Table
CREATE TABLE IF NOT EXISTS series (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    series_type VARCHAR(100)
);

-- 2. Venues Table
CREATE TABLE IF NOT EXISTS venues (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    capacity INT
);

-- 3. Teams Table
CREATE TABLE IF NOT EXISTS teams (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50)
);

-- 4. Players Table
CREATE TABLE IF NOT EXISTS players (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    batting_style VARCHAR(100),
    bowling_style VARCHAR(100),
    image_url TEXT
);

-- 5. Matches Table (Supports both Live and Historical Matches)
CREATE TABLE IF NOT EXISTS matches (
    id INT PRIMARY KEY,
    series_id INT REFERENCES series(id) ON DELETE SET NULL,
    venue_id INT REFERENCES venues(id) ON DELETE SET NULL,
    match_desc VARCHAR(255),
    format VARCHAR(50),
    status VARCHAR(255),
    team1_id INT REFERENCES teams(id) ON DELETE CASCADE,
    team2_id INT REFERENCES teams(id) ON DELETE CASCADE,
    toss_winner_id INT REFERENCES teams(id) ON DELETE SET NULL,
    toss_decision VARCHAR(50),
    winner_id INT REFERENCES teams(id) ON DELETE SET NULL,
    match_start_time TIMESTAMP WITH TIME ZONE,
    is_live BOOLEAN DEFAULT FALSE,
    is_completed BOOLEAN DEFAULT TRUE,
    match_overs_limit INT DEFAULT 20,
    player_of_the_match_id INT REFERENCES players(id) ON DELETE SET NULL
);

-- 6. Innings Table
CREATE TABLE IF NOT EXISTS innings (
    id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(id) ON DELETE CASCADE,
    innings_num INT NOT NULL,
    batting_team_id INT REFERENCES teams(id) ON DELETE CASCADE,
    bowling_team_id INT REFERENCES teams(id) ON DELETE CASCADE,
    runs INT DEFAULT 0,
    wickets INT DEFAULT 0,
    overs NUMERIC(4, 1) DEFAULT 0.0,
    extras INT DEFAULT 0,
    wides INT DEFAULT 0,
    no_balls INT DEFAULT 0,
    byes INT DEFAULT 0,
    leg_byes INT DEFAULT 0,
    CONSTRAINT unique_match_innings UNIQUE (match_id, innings_num)
);

-- 7. Batting Scores Table (Tracks dismissals, bowlers, and fielders)
CREATE TABLE IF NOT EXISTS batting_scores (
    id SERIAL PRIMARY KEY,
    innings_id INT REFERENCES innings(id) ON DELETE CASCADE,
    player_id INT REFERENCES players(id) ON DELETE CASCADE,
    runs INT DEFAULT 0,
    balls INT DEFAULT 0,
    fours INT DEFAULT 0,
    sixes INT DEFAULT 0,
    strike_rate NUMERIC(6, 2) DEFAULT 0.0,
    out BOOLEAN DEFAULT TRUE,
    dismissal_type VARCHAR(50), -- e.g., 'caught', 'bowled', 'lbw', 'run out', 'stumped'
    dismissal_text TEXT,
    bowler_id INT REFERENCES players(id) ON DELETE SET NULL, -- Bowler who got the wicket
    fielder_id INT REFERENCES players(id) ON DELETE SET NULL, -- Fielder involved in catch/runout
    CONSTRAINT unique_innings_batsman UNIQUE (innings_id, player_id)
);

-- 8. Bowling Scores Table
CREATE TABLE IF NOT EXISTS bowling_scores (
    id SERIAL PRIMARY KEY,
    innings_id INT REFERENCES innings(id) ON DELETE CASCADE,
    player_id INT REFERENCES players(id) ON DELETE CASCADE,
    overs NUMERIC(4, 1) DEFAULT 0.0,
    maidens INT DEFAULT 0,
    runs_conceded INT DEFAULT 0,
    wickets INT DEFAULT 0,
    economy NUMERIC(5, 2) DEFAULT 0.0,
    CONSTRAINT unique_innings_bowler UNIQUE (innings_id, player_id)
);

-- 9. Fielding Records Table (Catches, stumpings, and run-outs per innings)
CREATE TABLE IF NOT EXISTS fielding_records (
    id SERIAL PRIMARY KEY,
    innings_id INT REFERENCES innings(id) ON DELETE CASCADE,
    player_id INT REFERENCES players(id) ON DELETE CASCADE,
    catches INT DEFAULT 0,
    stumpings INT DEFAULT 0,
    run_outs INT DEFAULT 0,
    CONSTRAINT unique_innings_fielder UNIQUE (innings_id, player_id)
);

-- 10. Partnerships Table (Tracks batting partnerships)
CREATE TABLE IF NOT EXISTS partnerships (
    id SERIAL PRIMARY KEY,
    innings_id INT REFERENCES innings(id) ON DELETE CASCADE,
    batsman1_id INT REFERENCES players(id) ON DELETE CASCADE,
    batsman2_id INT REFERENCES players(id) ON DELETE CASCADE,
    runs INT DEFAULT 0,
    balls INT DEFAULT 0,
    boundaries_fours INT DEFAULT 0,
    boundaries_sixes INT DEFAULT 0,
    unbroken BOOLEAN DEFAULT FALSE,
    CONSTRAINT unique_partnership UNIQUE (innings_id, batsman1_id, batsman2_id)
);

-- Indexes for performance optimizations
CREATE INDEX IF NOT EXISTS idx_matches_series ON matches(series_id);
CREATE INDEX IF NOT EXISTS idx_matches_venue ON matches(venue_id);
CREATE INDEX IF NOT EXISTS idx_matches_live ON matches(is_live);
CREATE INDEX IF NOT EXISTS idx_innings_match ON innings(match_id);
CREATE INDEX IF NOT EXISTS idx_batting_innings ON batting_scores(innings_id);
CREATE INDEX IF NOT EXISTS idx_batting_player ON batting_scores(player_id);
CREATE INDEX IF NOT EXISTS idx_batting_bowler ON batting_scores(bowler_id);
CREATE INDEX IF NOT EXISTS idx_batting_fielder ON batting_scores(fielder_id);
CREATE INDEX IF NOT EXISTS idx_bowling_innings ON bowling_scores(innings_id);
CREATE INDEX IF NOT EXISTS idx_bowling_player ON bowling_scores(player_id);
CREATE INDEX IF NOT EXISTS idx_fielding_innings ON fielding_records(innings_id);
CREATE INDEX IF NOT EXISTS idx_fielding_player ON fielding_records(player_id);
CREATE INDEX IF NOT EXISTS idx_partnerships_innings ON partnerships(innings_id);
CREATE INDEX IF NOT EXISTS idx_partnerships_players ON partnerships(batsman1_id, batsman2_id);
CREATE INDEX IF NOT EXISTS idx_matches_head_to_head ON matches(team1_id, team2_id);
