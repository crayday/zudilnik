
-- 2022-10-29
PRAGMA foreign_keys=off;

-- users --
CREATE TABLE users (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);
INSERT INTO users VALUES (1, 'ego_rod');

-- projects --
DROP INDEX projects__created_at_idx;
ALTER TABLE projects RENAME TO _projects;

CREATE TABLE projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  parent_id INTEGER NULL,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  FOREIGN KEY (parent_id) REFERENCES projects(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE (user_id, name)
);
CREATE INDEX projects__created_at_idx ON projects(created_at);

INSERT INTO projects (id, parent_id, user_id, name, created_at)
SELECT id, NULL, 1, name, created_at FROM _projects ORDER BY id ASC;

DROP TABLE _projects;

-- subprojects to projects --
INSERT INTO projects (id, parent_id, user_id, name, created_at)
SELECT id + 10, project_id, 1, name, created_at FROM subprojects ORDER BY id ASC;
DROP INDEX subprojects__created_at_idx;
DROP TABLE subprojects;

-- timelog --
DROP INDEX timelog__started_at_idx;
ALTER TABLE timelog RENAME TO _timelog;

CREATE TABLE timelog (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  project_id INTEGER NOT NULL,
  started_at INTEGER NOT NULL,
  stoped_at INTEGER,
  duration INTEGER,
  comment TEXT,
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX timelog__started_at_idx ON timelog(started_at);

INSERT INTO timelog (id, user_id, project_id, started_at, stoped_at, duration, comment)
SELECT id, 1, subproject_id+10, started_at, stoped_at, duration, comment FROM _timelog ORDER BY id ASC;

DROP TABLE _timelog;

-- goals --
DROP INDEX goals__created_at_idx;
ALTER TABLE goals RENAME TO _goals;

CREATE TABLE goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  project_id INTEGER,
  name TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  archived_at INTEGER,
  type TEXT NOT NULL DEFAULT "hours_light",
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE (user_id, name)
);
CREATE INDEX goals__created_at_idx ON goals(created_at);

INSERT INTO goals (id, user_id, project_id, name, created_at, archived_at)
SELECT id, 1, COALESCE(subproject_id, project_id), name, created_at, archived_at FROM _goals ORDER BY id ASC;

DROP TABLE _goals;

PRAGMA foreign_keys=off;
