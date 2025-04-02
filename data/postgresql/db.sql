--
-- PostgreSQL database schema for expense app
--

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
-- Name: receipt; Type: TABLE; Schema: public
--

CREATE TABLE IF NOT EXISTS public.receipt (
    id integer NOT NULL,
    date timestamp without time zone,
    total_amount numeric(10,2),
    currency character varying(3),
    description text,
    image_path character varying(255),
    user_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

--
-- Name: receipt_id_seq; Type: SEQUENCE; Schema: public
--

CREATE SEQUENCE IF NOT EXISTS public.receipt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.receipt_id_seq OWNED BY public.receipt.id;

--
-- Name: user; Type: TABLE; Schema: public
--

CREATE TABLE IF NOT EXISTS public."user" (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255),
    first_name character varying(100),
    last_name character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public
--

CREATE SEQUENCE IF NOT EXISTS public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

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
-- Name: receipt receipt_user_id_fkey; Type: FK CONSTRAINT; Schema: public
--

ALTER TABLE ONLY public.receipt
    ADD CONSTRAINT receipt_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);

--
-- PostgreSQL database dump complete
--

