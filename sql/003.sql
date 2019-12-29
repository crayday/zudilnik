PRAGMA foreign_keys=off;

ALTER TABLE goals RENAME TO _goals_old;

CREATE TABLE goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER,
  subproject_id INTEGER,
  name TEXT NOT NULL UNIQUE,
  created_at INTEGER NOT NULL,
  archived_at INTEGER,
  type TEXT NOT NULL DEFAULT "hours_light",
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (subproject_id) REFERENCES subprojects(id)
);

INSERT INTO goals (id, project_id, subproject_id, name, created_at, archived_at)
  SELECT id, project_id, subproject_id, name, created_at, archived_at
  FROM _goals_old;

DROP TABLE _goals_old;

CREATE INDEX goals__created_at_idx ON goals(created_at);

PRAGMA foreign_keys=off;
