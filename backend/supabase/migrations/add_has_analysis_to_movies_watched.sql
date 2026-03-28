ALTER TABLE public.movies_watched
  ADD COLUMN IF NOT EXISTS has_analysis BOOLEAN NOT NULL DEFAULT FALSE;

-- Ejecutar manualmente en Supabase Dashboard > SQL Editor
