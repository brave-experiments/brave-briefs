CREATE EXTENSION vector;

create table embeddings (
    id         uuid        not null primary key default gen_random_uuid(),
    batch_id   text        not null,
    hash       text        not null,
    embedding  vector(384) not null,
    cluster    text,
    created_at timestamp   not null default current_timestamp,
    unique (batch_id, hash)
);

create table jobs (
    id         uuid        not null primary key,
    type       text        not null,
    status     text        not null,
    created_at timestamp   not null default current_timestamp,
    updated_at timestamp   not null default current_timestamp,
    unique (id)
);
