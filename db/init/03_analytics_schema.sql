-- =============================================
-- SCHEMA: analytics
-- Tabelas prontas para análise e modelagem
-- =============================================

CREATE SCHEMA IF NOT EXISTS analytics;

-- Desempenho geral do time na temporada
CREATE TABLE IF NOT EXISTS analytics.team_performance (
    id                  SERIAL PRIMARY KEY,
    team_id             INTEGER         REFERENCES dwh.dim_teams(team_id),
    matches_played      INTEGER,
    wins                INTEGER,
    draws               INTEGER,
    losses              INTEGER,
    goals_scored        INTEGER,
    goals_conceded      INTEGER,
    goal_diff           INTEGER,
    points              INTEGER,
    win_rate            NUMERIC(5,2),
    avg_xg_for          NUMERIC(5,2),
    avg_xg_against      NUMERIC(5,2),
    avg_possession      NUMERIC(5,2),
    avg_ppda            NUMERIC(6,2),
    updated_at          TIMESTAMP       DEFAULT NOW()
);

-- Fatores de vitória por partida
CREATE TABLE IF NOT EXISTS analytics.win_factors (
    id                  SERIAL PRIMARY KEY,
    match_id            INTEGER         REFERENCES dwh.fact_matches(match_id),
    team_id             INTEGER         REFERENCES dwh.dim_teams(team_id),
    result              VARCHAR(10),    -- WIN, DRAW, LOSS
    xg_diff             NUMERIC(5,2),
    possession          NUMERIC(5,2),
    shot_accuracy       NUMERIC(5,2),
    ppda                NUMERIC(6,2),
    corners             INTEGER,
    fouls               INTEGER,
    is_home             BOOLEAN,
    created_at          TIMESTAMP       DEFAULT NOW()
);

-- Correlações entre métricas e resultado
CREATE TABLE IF NOT EXISTS analytics.metric_correlations (
    id                  SERIAL PRIMARY KEY,
    metric_name         VARCHAR(100),
    correlation_with    VARCHAR(50),    -- WIN, GOALS, XG
    correlation_value   NUMERIC(6,4),
    sample_size         INTEGER,
    calculated_at       TIMESTAMP       DEFAULT NOW()
);

-- Ranking de jogadores por impacto
CREATE TABLE IF NOT EXISTS analytics.player_impact (
    id                  SERIAL PRIMARY KEY,
    player_id           INTEGER         REFERENCES dwh.dim_players(player_id),
    team_id             INTEGER         REFERENCES dwh.dim_teams(team_id),
    matches_played      INTEGER,
    goals               INTEGER,
    assists             INTEGER,
    goal_contributions  INTEGER,
    avg_pass_accuracy   NUMERIC(5,2),
    avg_shot_accuracy   NUMERIC(5,2),
    win_rate_when_plays NUMERIC(5,2),
    impact_score        NUMERIC(6,2),
    updated_at          TIMESTAMP       DEFAULT NOW()
);

-- View: resumo de partida para análise rápida
CREATE OR REPLACE VIEW analytics.v_match_summary AS
SELECT
    fm.match_id,
    dd.full_date                        AS match_date,
    fm.round,
    ht.team_name                        AS home_team,
    at.team_name                        AS away_team,
    fm.home_goals,
    fm.away_goals,
    fm.home_xg,
    fm.away_xg,
    fm.home_xg - fm.away_xg            AS xg_diff,
    fm.result,
    fm.attendance
FROM dwh.fact_matches fm
JOIN dwh.dim_date     dd ON fm.date_id      = dd.date_id
JOIN dwh.dim_teams    ht ON fm.home_team_id = ht.team_id
JOIN dwh.dim_teams    at ON fm.away_team_id = at.team_id;

-- View: métricas avançadas por time na temporada
CREATE OR REPLACE VIEW analytics.v_team_season_stats AS
SELECT
    dt.team_name,
    COUNT(DISTINCT fm.match_id)         AS matches_played,
    AVG(fas.possession)                 AS avg_possession,
    AVG(fas.xg)                         AS avg_xg,
    AVG(fas.xg_against)                 AS avg_xg_against,
    AVG(fas.xg - fas.xg_against)        AS avg_xg_diff,
    AVG(fas.ppda)                        AS avg_ppda,
    AVG(fas.shot_accuracy)              AS avg_shot_accuracy,
    SUM(CASE WHEN wf.result = 'WIN'  THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN wf.result = 'DRAW' THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN wf.result = 'LOSS' THEN 1 ELSE 0 END) AS losses
FROM dwh.fact_advanced_stats  fas
JOIN dwh.dim_teams             dt  ON fas.team_id  = dt.team_id
JOIN dwh.fact_matches          fm  ON fas.match_id = fm.match_id
LEFT JOIN analytics.win_factors wf ON fas.match_id = wf.match_id
                                   AND fas.team_id  = wf.team_id
GROUP BY dt.team_name;
