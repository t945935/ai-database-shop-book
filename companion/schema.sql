CREATE TABLE balance (
 sku text PRIMARY KEY,
 physical integer NOT NULL DEFAULT 0 CHECK (physical >= 0),
 reserved integer NOT NULL DEFAULT 0 CHECK (reserved >= 0 AND reserved <= physical),
 value numeric(24,6) NOT NULL DEFAULT 0 CHECK (value >= 0),
 CHECK (physical <> 0 OR value = 0)
);
CREATE TABLE reservation (
 event text PRIMARY KEY,
 sku text NOT NULL REFERENCES balance,
 qty integer NOT NULL CHECK(qty>0),
 consumed boolean NOT NULL DEFAULT false
);
CREATE TABLE shipment (
 event text PRIMARY KEY,
 reservation text NOT NULL UNIQUE REFERENCES reservation(event),
 sku text NOT NULL REFERENCES balance,
 qty integer NOT NULL CHECK(qty>0),
 cost numeric(24,6) NOT NULL CHECK(cost>=0)
);
CREATE TABLE returned (
 event text PRIMARY KEY,
 shipment text NOT NULL REFERENCES shipment(event),
 qty integer NOT NULL CHECK(qty>0),
 cost numeric(24,6) NOT NULL CHECK(cost>=0)
);
CREATE TABLE ledger (
 event text PRIMARY KEY,
 kind text NOT NULL,
 sku text NOT NULL REFERENCES balance,
 payload jsonb NOT NULL,
 physical_delta integer NOT NULL,
 reserved_delta integer NOT NULL,
 value_delta numeric(24,6) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
