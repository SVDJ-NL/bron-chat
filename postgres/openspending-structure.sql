-- -------------------------------------------------------------
-- TablePlus 4.7.1(428)
--
-- https://tableplus.com/
--
-- Database: openspending
-- Generation Time: 2024-11-07 12:30:31.0000
-- -------------------------------------------------------------

CREATE TABLE "public"."detaildatafile" (
    "Key" varchar(9) NOT NULL,
    "Workspace" varchar(8) NOT NULL,
    "Verslagsoort" varchar(9) NOT NULL,
    "sourcefile" text NOT NULL,
    PRIMARY KEY ("Key","Workspace","Verslagsoort")
);

CREATE TABLE "public"."ft_search" (
    "Workspace" varchar(8) NOT NULL,
    "Tabel" varchar(15) NOT NULL,
    "Title" text NOT NULL,
    "Description" text NOT NULL
);

CREATE TABLE "public"."ft_search_detaildata" (
    "Workspace" varchar(8) NOT NULL,
    "Source" varchar(9) NOT NULL,
    "Code" varchar(20) NOT NULL,
    "Title" text NOT NULL,
    "Type" varchar(15) NOT NULL
);

CREATE TABLE "public"."gemeenschappelijkeregeling" (
    "Key" varchar(9) NOT NULL,
    "lat" numeric NOT NULL,
    "lon" numeric NOT NULL,
    "adres" text NOT NULL,
    PRIMARY KEY ("Key")
);

CREATE TABLE "public"."login" (
    "Username" text NOT NULL,
    "Password" text NOT NULL,
    "Source" varchar(9),
    "Role" varchar(9),
    PRIMARY KEY ("Username")
);

CREATE TABLE "public"."metrics" (
    "Regio" varchar(9) NOT NULL,
    "Type" varchar(15) NOT NULL,
    "Jaar" int2 NOT NULL,
    "Aantal" int4 NOT NULL,
    PRIMARY KEY ("Regio","Type","Jaar")
);

CREATE TABLE "public"."session" (
    "Token" text NOT NULL,
    "Username" text NOT NULL,
    "Expires" timestamptz NOT NULL,
    PRIMARY KEY ("Token")
);

CREATE TABLE "public"."source" (
    "Key" varchar(9) NOT NULL,
    "Title" varchar(100),
    "Slug" varchar(100),
    "Type" varchar(30),
    "Description" text,
    PRIMARY KEY ("Key")
);

CREATE TABLE "public"."sourcehasgemeenschappelijkeregeling" (
    "Source" varchar(9) NOT NULL,
    "GR" varchar(9) NOT NULL,
    PRIMARY KEY ("Source","GR")
);

CREATE TABLE "public"."sourcehaslogin" (
    "Key" varchar(9) NOT NULL,
    "Password" text NOT NULL,
    PRIMARY KEY ("Key")
);

CREATE TABLE "public"."sourcehasworkspace" (
    "Key" varchar(9) NOT NULL,
    "Workspace" varchar(8) NOT NULL,
    "hasDetaildata" bool NOT NULL DEFAULT false,
    "detailDataPublished" bool NOT NULL DEFAULT false,
    PRIMARY KEY ("Key","Workspace")
);

CREATE TABLE "public"."url" (
    "key" varchar(8) NOT NULL,
    "path" varchar(250) NOT NULL,
    PRIMARY KEY ("key","path")
);

CREATE TABLE "public"."workspace" (
    "Identifier" varchar(8) NOT NULL,
    "Period" int2 NOT NULL,
    "Title" varchar(100),
    "Summary" text,
    "StatLineID" varchar(25),
    "SourceType" varchar(30),
    "Modified" timestamptz NOT NULL,
    PRIMARY KEY ("Identifier")
);

ALTER TABLE "public"."detaildatafile" ADD FOREIGN KEY ("Key") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."detaildatafile" ADD FOREIGN KEY ("Workspace") REFERENCES "public"."workspace"("Identifier") ON DELETE CASCADE;
ALTER TABLE "public"."ft_search_detaildata" ADD FOREIGN KEY ("Workspace") REFERENCES "public"."workspace"("Identifier") ON DELETE CASCADE;
ALTER TABLE "public"."ft_search_detaildata" ADD FOREIGN KEY ("Source") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."gemeenschappelijkeregeling" ADD FOREIGN KEY ("Key") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."login" ADD FOREIGN KEY ("Source") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."session" ADD FOREIGN KEY ("Username") REFERENCES "public"."login"("Username") ON DELETE CASCADE;
ALTER TABLE "public"."sourcehasgemeenschappelijkeregeling" ADD FOREIGN KEY ("GR") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."sourcehasgemeenschappelijkeregeling" ADD FOREIGN KEY ("Source") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."sourcehaslogin" ADD FOREIGN KEY ("Key") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."sourcehasworkspace" ADD FOREIGN KEY ("Key") REFERENCES "public"."source"("Key") ON DELETE CASCADE;
ALTER TABLE "public"."sourcehasworkspace" ADD FOREIGN KEY ("Workspace") REFERENCES "public"."workspace"("Identifier") ON DELETE CASCADE;
