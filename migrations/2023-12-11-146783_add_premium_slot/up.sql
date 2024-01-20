ALTER TABLE premium ADD COLUMN slots integer NOT NULL DEFAULT 0;

UPDATE premium
SET slots = CASE
    WHEN cardinality(guilds) = 0 THEN 0
    WHEN cardinality(guilds) = 1 THEN 1
    WHEN cardinality(guilds) <= 3 THEN 3
    WHEN cardinality(guilds) <= 5 THEN 5
    ELSE 0
END;
