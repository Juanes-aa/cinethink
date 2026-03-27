-- Migration: Add genre_ids column and UNIQUE constraint to movies_watched
-- Run this manually in the Supabase SQL Editor.

ALTER TABLE movies_watched
ADD COLUMN IF NOT EXISTS genre_ids integer[] DEFAULT '{}';

ALTER TABLE movies_watched
ADD CONSTRAINT uq_movies_watched_user_tmdb UNIQUE (user_id, tmdb_id);
