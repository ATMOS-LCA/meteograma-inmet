-- auto-generated definition

create table estacoes
(
    codigo varchar(4) not null
        primary key,
    nome   text       not null
);

create table dados_estacoes
(
    id              serial
        primary key,
    estacao         text not null,
    data            date not null,
    utc             text not null,
    temperatura     numeric,
    temperatura_min numeric,
    temperatura_max numeric,
    umidade         numeric,
    umidade_min     numeric,
    umidade_max     numeric,
    pto_orvalho     numeric,
    pto_orvalho_min numeric,
    pto_orvalho_max numeric,
    pressao         numeric,
    pressao_min     numeric,
    pressao_max     numeric,
    vento           numeric,
    vento_dir       numeric,
    vento_raj       numeric,
    radiacao        numeric,
    chuva           numeric,
    constraint dados_estacoes_momento_uk
        unique (estacao, data, utc)
);

create table previsao
(
    id               serial
        primary key,
    data_previsao    date    not null,
    data_inicio      date    not null,
    tamanho_previsao integer not null,
    modelo           text,
    constraint previsao_uk
        unique (data_previsao, modelo, tamanho_previsao)
);

create table dados_temperatura_previsao
(
    id              serial
        primary key,
    previsao_id     integer not null
        constraint dados_temperatura_previsao_previsao_fk
            references previsao,
    estacao         varchar(4)
        constraint dados_temperatura_previsao_estacao_fk
            references estacoes,
    data            date    not null,
    temperatura_max double precision,
    temperatura_min double precision,
    acumpre         double precision,
    nebulos         double precision,
    constraint dados_temperatura_previsao_previsao_data_key
        unique (previsao_id, estacao, data)
);

create table dados_detalhados_previsao
(
    id                 serial
        primary key,
    previsao_id        integer    not null
        constraint dados_detalhados_previsao_previsao_fk
            references previsao,
    estacao            varchar(4)
        constraint dados_detalhados_previsao_estacao_fk
            references estacoes,
    data               date       not null,
    utc                varchar(4) not null,
    precipitacao       double precision,
    temperatura        double precision,
    umidade_relativa   double precision,
    pressao_superficie double precision,
    u10m               double precision,
    v10m               double precision,
    vento              double precision,
    vento_dir          double precision,
    fracao_vento       double precision,
    radiacao_oc_inc    double precision,
    constraint dados_detalhados_previsao_previsao_data_key
        unique (previsao_id, estacao, data, utc)
)