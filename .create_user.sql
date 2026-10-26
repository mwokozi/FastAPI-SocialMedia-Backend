DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'socialite'
    ) THEN
        CREATE USER socialite WITH 
PASSWORD 'sn123$'
--CREATEDB       --not admin dont need
--CREATEROLE   --not admin dont need
;
    END IF;
END
$$;


;
--CREATE DATABASE  social_network OWNER socialite; --create database social_network make socialite its owner

SELECT 'CREATE DATABASE social_network OWNER socialite'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'social_network'
)\gexec 

--\gexec specfic to postgres


\c social_network socialite  

-- log into newly created database 

CREATE SCHEMA IF NOT EXISTS social_network AUTHORIZATION socialite; --create schema make socialite its owner

ALTER USER socialite IN DATABASE social_network  SET search_path TO social_network;  



