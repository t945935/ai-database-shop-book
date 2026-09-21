CREATE TABLE supplier_document (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_name text NOT NULL CHECK (btrim(supplier_name) <> ''),
    version text NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    title text NOT NULL,
    UNIQUE (supplier_name, version),
    CHECK (effective_to IS NULL OR effective_to > effective_from)
);
CREATE TABLE document_chunk (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id bigint NOT NULL REFERENCES supplier_document(id) ON DELETE CASCADE,
    chunk_no integer NOT NULL CHECK (chunk_no > 0),
    body text NOT NULL CHECK (btrim(body) <> ''),
    UNIQUE (document_id, chunk_no)
);
INSERT INTO supplier_document(supplier_name,version,effective_from,effective_to,title) VALUES
('山城烘豆商','v1','2026-01-01','2026-07-01','退貨條款舊版'),
('山城烘豆商','v2','2026-07-01',NULL,'退貨條款現行版');
INSERT INTO document_chunk(document_id,chunk_no,body)
SELECT id,1,CASE version WHEN 'v1' THEN '瑕疵品須於七日內提出。' ELSE '瑕疵品須於十四日內提出，並附上批次照片。' END
FROM supplier_document;
