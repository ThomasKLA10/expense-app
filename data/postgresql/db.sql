--
-- PostgreSQL database dump
--

-- Dumped from database version 13.18 (Debian 13.18-1.pgdg120+1)
-- Dumped by pg_dump version 13.18 (Debian 13.18-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);

--
-- Name: receipt; Type: TABLE; Schema: public
--

CREATE TABLE public.receipt (
    id integer NOT NULL,
    amount double precision NOT NULL,
    currency character varying(3) NOT NULL,
    category character varying(50) NOT NULL,
    file_path character varying(200) NOT NULL,
    date_submitted timestamp without time zone,
    status character varying(20),
    office character varying(50) NOT NULL,
    user_id integer,
    purpose character varying(200),
    travel_from character varying(100),
    travel_to character varying(100),
    departure_date date,
    return_date date
);

--
-- Name: receipt_id_seq; Type: SEQUENCE; Schema: public
--

CREATE SEQUENCE public.receipt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: receipt_id_seq; Type: SEQUENCE OWNED BY; Schema: public
--

ALTER SEQUENCE public.receipt_id_seq OWNED BY public.receipt.id;

--
-- Name: user; Type: TABLE; Schema: public
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    email character varying(120) NOT NULL,
    name character varying(120)
);

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;

--
-- Name: receipt id; Type: DEFAULT; Schema: public
--

ALTER TABLE ONLY public.receipt ALTER COLUMN id SET DEFAULT nextval('public.receipt_id_seq'::regclass);

--
-- Name: user id; Type: DEFAULT; Schema: public
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);

--
-- Name: receipt receipt_pkey; Type: CONSTRAINT; Schema: public
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_pkey PRIMARY KEY (id);

--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);

--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);

--
-- Name: receipt receipt_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);

--
-- PostgreSQL database dump complete
--

