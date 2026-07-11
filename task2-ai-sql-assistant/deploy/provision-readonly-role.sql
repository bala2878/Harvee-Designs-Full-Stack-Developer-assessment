DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sqlassistant_readonly') THEN
        CREATE ROLE sqlassistant_readonly WITH LOGIN PASSWORD :readonly_password;
    ELSE
        EXECUTE format('ALTER ROLE sqlassistant_readonly WITH PASSWORD %L', :'readonly_password');
    END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS datasets;
GRANT USAGE ON SCHEMA datasets TO sqlassistant_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA datasets GRANT SELECT ON TABLES TO sqlassistant_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA datasets TO sqlassistant_readonly;

REVOKE ALL ON SCHEMA public FROM sqlassistant_readonly;

ALTER ROLE sqlassistant_readonly NOCREATEDB NOCREATEROLE NOSUPERUSER;
