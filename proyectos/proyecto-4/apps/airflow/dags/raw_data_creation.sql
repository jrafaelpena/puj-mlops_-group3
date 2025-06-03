DROP TABLE IF EXISTS raw_data;

DROP TABLE IF EXISTS clean_data;

CREATE TABLE raw_data (
    brokered_by       TEXT,
    status            TEXT,
    price             NUMERIC,
    bed               SMALLINT,
    bath              SMALLINT,
    acre_lot          NUMERIC,
    street            TEXT,
    city              TEXT,
    state             TEXT,
    zip_code          VARCHAR(10),
    house_size        INTEGER,
    prev_sold_date    DATE,
    batch             SMALLINT
);