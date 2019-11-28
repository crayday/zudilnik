-- record in this tables means failure of particular goal that day
CREATE TABLE goal_failures (
  goal_id INTEGER NOT NULL,
  failed_at TEXT NOT NULL, -- YYYY-MM-DD
  PRIMARY KEY (goal_id, date)
);

CREATE TABLE punishments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  description TEXT NOT NULL
);

CREATE TABLE punishment_executions (
  punishment_id INTEGER NOT NULL,
  executed_at TEXT NOT NULL, -- YYYY-MM-DD
  failed_goal_id INTEGER,
  comment TEXT,
  PRIMARY KEY (failed_goal_id, executed_at),
  FOREIGN KEY (punishment_id) REFERENCES punishments(id),
  FOREIGN KEY (failed_goal_id) REFERENCES goals(id)
);
