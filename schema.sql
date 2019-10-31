pragma foreign_keys = ON;

CREATE TABLE projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  created_at INTEGER NOT NULL
);
CREATE INDEX projects__created_at_idx ON projects(created_at);

CREATE TABLE subprojects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL UNIQUE,
  created_at INTEGER NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE INDEX subprojects__created_at_idx ON subprojects(created_at);

CREATE TABLE timelog (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subproject_id INTEGER NOT NULL,
  started_at INTEGER NOT NULL,
  stoped_at INTEGER,
  duration INTEGER,
  comment TEXT,
  FOREIGN KEY (subproject_id) REFERENCES subprojects(id)
);
CREATE INDEX timelog__started_at_idx ON timelog(started_at);

CREATE TABLE goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER,
  subproject_id INTEGER,
  name TEXT NOT NULL UNIQUE,
  created_at INTEGER NOT NULL,
  archived_at INTEGER,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (subproject_id) REFERENCES subprojects(id)
);
CREATE INDEX goals__created_at_idx ON goals(created_at);

CREATE TABLE hoursperday (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_id INTEGER NOT NULL,
  weekday INTEGER NOT NULL, -- 1 - monday, 7 - sunday
  hours REAL NOT NULL,
  date_from TEXT NOT NULL, -- YYYY-MM-DD
  date_to TEXT, -- YYYY-MM-DD
  FOREIGN KEY (goal_id) REFERENCES goals(id)
);
