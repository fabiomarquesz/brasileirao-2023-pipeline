-- =============================================
-- SCHEMA: raw
-- Dados brutos vindos direto do FBref
-- =============================================

CREATE SCHEMA IF NOT EXISTS raw;

-- Partidas brutas
CREATE TABLE IF NOT EXISTS raw.matches (
    id                  SERIAL PRIMARY KEY,
    season              VARCHAR(10)     NOT NULL DEFAULT '2023',
    round               VARCHAR(50),
    match_date          DATE,
    home_team           VARCHAR(100),
    away_team           VARCHAR(100),
    home_goals          INTEGER,
    away_goals          INTEGER,
    home_xg             NUMERIC(5,2),
    away_xg             NUMERIC(5,2),
    venue               VARCHAR(150),
    attendance          INTEGER,
    referee             VARCHAR(100),
    match_url           VARCHAR(500),
    scraped_at          TIMESTAMP       DEFAULT NOW()
);

-- Estatísticas brutas por jogador por partida
CREATE TABLE IF NOT EXISTS raw.player_stats (
    id                  SERIAL PRIMARY KEY,
    match_url           VARCHAR(500),
    team                VARCHAR(100),
    player_name         VARCHAR(150),
    position            VARCHAR(20),
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
    scraped_at          TIMESTAMP       DEFAULT NOW()
);

-- Métricas avançadas brutas por partida
CREATE TABLE IF NOT EXISTS raw.advanced_stats (
    id                  SERIAL PRIMARY KEY,
    match_url           VARCHAR(500),
    team                VARCHAR(100),
    is_home             BOOLEAN,
    possession          NUMERIC(5,2),
    xg                  NUMERIC(5,2),
    xg_against          NUMERIC(5,2),
    shots               INTEGER,
    shots_on_target     INTEGER,
    deep_completions    INTEGER,
    ppda                NUMERIC(6,2),
    corners             INTEGER,
    fouls               INTEGER,
    offsides            INTEGER,
    scraped_at          TIMESTAMP       DEFAULT NOW()
);
