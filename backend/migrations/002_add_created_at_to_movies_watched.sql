-- Migration: Add created_at column to movies_watched
-- Run this manually in the Supabase SQL Editor.

ALTER TABLE movies_watched
ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
