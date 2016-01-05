CREATE DATABASE IF NOT EXISTS webocr;

USE webocr;

CREATE TABLE IF NOT EXISTS entities (
    added_id BIGINT NOT NULL AUTO_INCREMENT,
    id BINARY(16) NOT NULL,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tag MEDIUMINT,
    body MEDIUMBLOB NOT NULL,
    PRIMARY KEY (added_id),
    UNIQUE KEY (id),
    KEY (updated)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS index_url (
    entity_id BINARY(16) NOT NULL UNIQUE,
    url VARCHAR(512) NOT NULL,
    PRIMARY KEY (url, entity_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS index_service_id (
    entity_id BINARY(16) NOT NULL UNIQUE,
    service_id VARCHAR(512) NOT NULL,
    PRIMARY KEY (service_id, entity_id)
) ENGINE=InnoDB;

