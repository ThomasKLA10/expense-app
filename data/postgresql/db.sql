-- PostgreSQL database schema for expense app (simplified)

-- User table
CREATE TABLE IF NOT EXISTS public."user" (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Receipt table
CREATE TABLE IF NOT EXISTS public.receipt (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    amount NUMERIC(10,2),
    currency VARCHAR(3),
    date DATE,
    category VARCHAR(255),
    description TEXT,
    image_path VARCHAR(255),
    pdf_path VARCHAR(255),
    user_id INTEGER REFERENCES public."user"(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

--
-- PostgreSQL database dump complete
--

