-- Confere BU — Postgres schema. Append-only: rows are never updated or deleted; state changes are new rows.
-- Section key format (same everywhere): '<turn>:<uf>:<municipality>:<zone>:<section>', e.g. '2:mg:53112:170:37'.

CREATE TABLE IF NOT EXISTS submissions (            -- every POST accepted by the edge
  id            bigserial PRIMARY KEY,
  received_at   timestamptz NOT NULL DEFAULT now(),
  final_hash    char(128)   NOT NULL,              -- signed hash of the ballot (dedupe key)
  section_key   text        NOT NULL,
  raw_key       text        NOT NULL,              -- R2 object key of the raw QR texts
  ip_hash       text                                -- sha256(ip + daily salt); never the raw IP
);
CREATE INDEX IF NOT EXISTS submissions_section ON submissions (section_key);
CREATE INDEX IF NOT EXISTS submissions_ballot ON submissions (final_hash);  -- recompute joins by ballot; without it: full scan per submission (loadtest)

CREATE TABLE IF NOT EXISTS ballots (                -- one row per distinct door ballot (by final hash)
  final_hash       char(128) PRIMARY KEY,
  section_key      text      NOT NULL,
  version          text      NOT NULL,             -- '1.5' | '6.0'
  urna_id          text      NOT NULL,             -- IDUE
  cert_fingerprint text,                           -- sha256 of the urna certificate (QRCE)
  signature_status text      NOT NULL CHECK (signature_status IN ('valid', 'invalid', 'unverified')),
  origin           text      NOT NULL,             -- ORIG: VOTA | RED | SA
  fields           jsonb     NOT NULL,
  votes            jsonb     NOT NULL,             -- {office: {number|BRAN|NULO: count}}
  first_seen       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ballots_section ON ballots (section_key);
CREATE INDEX IF NOT EXISTS ballots_urna ON ballots (urna_id);

CREATE TABLE IF NOT EXISTS tse_ballots (            -- BU published by the TSE, per upload hash
  id           bigserial PRIMARY KEY,
  section_key  text        NOT NULL,
  file_hash    text        NOT NULL,               -- hash from aux.json
  received_at  text        NOT NULL,               -- TSE reception time as published ('dd/mm/yyyy hh:mm:ss')
  votes        jsonb       NOT NULL,
  fetched_at   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (section_key, file_hash)
);

CREATE TABLE IF NOT EXISTS comparisons (            -- every recomputation; latest row per section wins
  id           bigserial PRIMARY KEY,
  section_key  text        NOT NULL,
  status       text        NOT NULL CHECK (status IN ('waiting', 'tse-only', 'identical', 'divergent', 'conflict')),
  differences  jsonb       NOT NULL DEFAULT '[]',
  door_hash    char(128),
  tse_file_hash text,
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS comparisons_section ON comparisons (section_key, id DESC);

CREATE TABLE IF NOT EXISTS divergence_events (      -- opened → explained (with public document) → reopened...
  id           bigserial PRIMARY KEY,
  section_key  text        NOT NULL,
  kind         text        NOT NULL CHECK (kind IN ('opened', 'explained', 'reopened')),
  note         text,
  document_url text,
  actor        text,                                -- neutrality council member(s); NULL for automatic events
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW latest_comparisons AS
  SELECT DISTINCT ON (section_key) * FROM comparisons ORDER BY section_key, id DESC;

-- Enforce append-only at the database level.
CREATE OR REPLACE FUNCTION forbid_change() RETURNS trigger LANGUAGE plpgsql AS
  $$ BEGIN RAISE EXCEPTION 'append-only table: % on %', TG_OP, TG_TABLE_NAME; END $$;
DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['submissions', 'ballots', 'tse_ballots', 'comparisons', 'divergence_events'] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS %I_append_only ON %I', t, t);
    EXECUTE format('CREATE TRIGGER %I_append_only BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION forbid_change()', t, t);
  END LOOP;
END $$;
