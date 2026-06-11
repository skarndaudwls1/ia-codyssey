-- schema.sql
-- mars_weather 테이블 생성 스크립트.
-- MySQL Workbench 또는 mysql 클라이언트에서 실행한다.
--
-- 사용 예)
--   mysql -u root -p < schema.sql
--
-- 컬럼 정의
--   weather_id : 자동 증가하는 정수, Primary Key
--   mars_date  : 필수 입력(NOT NULL) datetime
--   temp       : 화성 기온 정수(INT). 명세에 맞춰 정수로 두고, CSV 의
--                소수 값은 적재 시 반올림한다.
--   storm      : 모래 폭풍 세기 정수

CREATE DATABASE IF NOT EXISTS mars_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE mars_db;

CREATE TABLE IF NOT EXISTS mars_weather (
    weather_id INT NOT NULL AUTO_INCREMENT,
    mars_date  DATETIME NOT NULL,
    temp       INT,
    storm      INT,
    PRIMARY KEY (weather_id)
);
