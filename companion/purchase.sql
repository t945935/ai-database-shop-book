CREATE TABLE supplier (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,name text NOT NULL CHECK (btrim(name)<>''));
CREATE TABLE purchase_order (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,supplier_id bigint NOT NULL REFERENCES supplier(id),status text NOT NULL DEFAULT 'open' CHECK(status IN ('open','closed','cancelled')));
CREATE TABLE purchase_item (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,order_id bigint NOT NULL REFERENCES purchase_order(id),sku_code text NOT NULL REFERENCES sku(code),ordered_qty integer NOT NULL CHECK(ordered_qty>0),unit_cost numeric NOT NULL CHECK(unit_cost>=0));
CREATE TABLE receipt (event text PRIMARY KEY,received_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE receipt_item (receipt_event text NOT NULL REFERENCES receipt(event),purchase_item_id bigint NOT NULL REFERENCES purchase_item(id),qty integer NOT NULL CHECK(qty>0),PRIMARY KEY(receipt_event,purchase_item_id));
