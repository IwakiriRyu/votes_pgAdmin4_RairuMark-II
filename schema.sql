CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE users (
	id integer PRIMARY key AUTOINCREMENT,
	username text UNIQUE not null,
	password text not NULL
	);
CREATE TABLE IF NOT EXISTS "Titles" (
	"id"	INTEGER,
	"section"	TEXT NOT NULL,
	"creator"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "questions" (
	"id"	INTEGER,
	"title"	TEXT NOT NULL,
	"option1"	TEXT NOT NULL,
	"option2"	TEXT NOT NULL,
	"option3"	TEXT NOT NULL,
	"option4"	TEXT NOT NULL,
	"answer"	TEXT NOT NULL,
	"explanation"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
