-- Migration: Add release_year column to movies_watched
-- Run this manually in the Supabase SQL Editor.

ALTER TABLE movies_watched
ADD COLUMN IF NOT EXISTS release_year integer;
