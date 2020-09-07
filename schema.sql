CREATE TABLE public.data
(
    guild bigint NOT NULL,
    prefix text,
    category bigint,
    accessrole bigint[] NOT NULL,
    logging bigint,
    welcome text,
    goodbye text,
    loggingplus boolean NOT NULL,
    pingrole bigint[] NOT NULL,
    blacklist bigint[] NOT NULL,
    anonymous boolean NOT NULL,
    PRIMARY KEY (guild)
);

CREATE TABLE public.snippet
(
    guild bigint NOT NULL,
    name text NOT NULL,
    content text NOT NULL
);

CREATE TABLE public.premium
(
    identifier bigint NOT NULL,
    guild bigint[] NOT NULL,
    expiry bigint,
    PRIMARY KEY (identifier)
);

CREATE TABLE public.ban
(
    identifier bigint NOT NULL,
    category integer NOT NULL,
    PRIMARY KEY (identifier)
);

CREATE TABLE public.preference
(
    identifier bigint NOT NULL,
    confirmation boolean NOT NULL,
    PRIMARY KEY (identifier)
);
