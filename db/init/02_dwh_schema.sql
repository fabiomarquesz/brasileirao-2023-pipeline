-- =============================================
-- SCHEMA: dwh
-- Modelo estrela para análise
-- =============================================

CREATE SCHEMA IF NOT EXISTS dwh;

-- Dimensão: Times
CREATE TABLE IF NOT EXISTS dwh.dim_teams (
    team_id             SERIAL PRIMARY KEY,
    team_name           VARCHAR(100)    NOT NULL UNIQUE,
    team_short          VARCHAR(10),
    city                VARCHAR(100),
    state               VARCHAR(50),
    stadium             VARCHAR(150),
    created_at          TIMESTAMP       DEFAULT NOW()
);

-- Dimensão: Jogadores
CREATE TABLE IF NOT EXISTS dwh.dim_players (
    player_id           SERIAL PRIMARY KEY,
    player_name         VARCHAR(150)    NOT NULL,
    team_id             INTEGER         REFERENCES dwh.dim_teams(team_id),
    position            VARCHAR(20),
    nationality         VARCHAR(100),
    created_at          TIMESTAMP       DEFAULT NOW()
);

-- Dimensão: Datas
CREATE TABLE IF NOT EXISTS dwh.dim_date (
    date_id             SERIAL PRIMARY KEY,
    full_date           DATE            NOT NULL UNIQUE,
    day                 INTEGER,
    month               INTEGER,
    year                INTEGER,
    quarter             INTEGER,
    day_of_week         INTEGER,
    day_name            VARCHAR(20),
    is_weekend          BOOLEAN
);

-- Fato: Partidas
CREATE TABLE IF NOT EXISTS dwh.fact_matches (
    match_id            SERIAL PRIMARY KEY,
    date_id             INTEGER         REFERENCES dwh.dim_date(date_id),
    home_team_id        INTEGER         REFERENCES dwh.dim_teams(team_id),
    away_team_id        INTEGER         REFERENCES dwh.dim_teams(team_id),
    round               VARCHAR(50),
    home_goals          INTEGER,
    away_goals          INTEGER,
    home_xg             NUMERIC(5,2),
    away_xg             NUMERIC(5,2),
    result              VARCHAR(10),    -- HOME_WIN, AWAY_WIN, DRAW
    venue               VARCHAR(150),
    attendance          INTEGER,
    referee             VARCHAR(100),
    match_url           VARCHAR(500),
    created_at          TIMESTAMP       DEFAULT NOW()
);

-- Fato: Estatísticas por jogador por partida
CREATE TABLE IF NOT EXISTS dwh.fact_player_stats (
    stat_id             SERIAL PRIMARY KEY,
    match_id            INTEGER         REFERENCES dwh.fact_matches(match_id),
    player_id           INTEGER         REFERENCES dwh.dim_players(player_id),
    team_id             INTEGER         REFERENCES dwh.dim_teams(team_id),
    minutes_played      INTEGER,
    goals               INTEGER,
    assists             INTEGER,
    shots               INTEGER,
    shots_on_target     INTEGER,
    passes_completed    INTEGER,
    passes_attempted    INTEGER,
    pass_accuracy       NUMERIC(5,2),
    dribbles_completed  INTEGER,
    dribbles_attempted  INTEGER,
    yellow_cards        INTEGER,
    red_cards           INTEGER,
    created_at          TIMESTAMP       DEFAULT NOW()
);

-- Fato: Métricas avançadas por time por partida
CREATE TABLE IF NOT EXISTS dwh.fact_advanced_stats (
    stat_id             SERIAL PRIMARY KEY,
    match_id            INTEGER         REFERENCES dwh.fact_matches(match_id),
    team_id             INTEGER         REFERENCES dwh.dim_teams(team_id),
    is_home             BOOLEAN,
    possession          NUMERIC(5,2),
    xg                  NUMERIC(5,2),
    xg_against          NUMERIC(5,2),
    xg_diff             NUMERIC(5,2),
    shots               INTEGER,
    shots_on_target     INTEGER,
    shot_accuracy       NUMERIC(5,2),
    deep_completions    INTEGER,
    ppda                NUMERIC(6,2),
    corners             INTEGER,
    fouls               INTEGER,
    offsides            INTEGER,
    created_at          TIMESTAMP       DEFAULT NOW()
);
