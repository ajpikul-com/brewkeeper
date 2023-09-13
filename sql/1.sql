CREATE TABLE hydrometer (id SERIAL PRIMARY KEY, time TIMESTAMPTZ, device VARCHAR, name VARCHAR, temperature INT, gravity INT);

CREATE INDEX ON hydrometer USING btree (time, name);
CREATE INDEX ON hydrometer USING btree (name);

CREATE TABLE photos (id SERIAL PRIMARY KEY, time TIMESTAMPTZ, name VARCHAR, filename VARCHAR, photo BYTEA);

CREATE INDEX ON photos USING btree (time, name);
CREATE INDEX ON photos USING btree (name);

CREATE TABLE events (id SERIAL PRIMARY KEY, time TIMESTAMPTZ, event VARCHAR);

CREATE INDEX ON events USING btree (time, event);
CREATE INDEX ON events USING btree (event);
