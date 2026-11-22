-- YojanaSetu AI — Supabase Schema
-- Run this in your Supabase SQL Editor (project → SQL Editor → New Query)
-- These tables are designed for Phase 3 (user accounts) — not needed for Phase 1 MVP

-- ── Sessions table ───────────────────────────────────────────────────────────
-- Stores anonymized eligibility check sessions (no personal ID required)
CREATE TABLE IF NOT EXISTS sessions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at  TIMESTAMPTZ DEFAULT now(),
  lang        TEXT DEFAULT 'en',         -- 'en' or 'hi'
  -- Anonymized profile (no Aadhaar, PAN, name, or bank details)
  profile     JSONB,
  results     JSONB,
  consent_given BOOLEAN DEFAULT FALSE    -- User must consent before data is saved
);

-- ── Users table (Phase 3 — requires explicit user consent) ──────────────────
-- Only created after the user signs in and consents to data storage
CREATE TABLE IF NOT EXISTS users (
  id              UUID PRIMARY KEY REFERENCES auth.users(id),
  created_at      TIMESTAMPTZ DEFAULT now(),
  phone_number    TEXT UNIQUE,            -- Optional, for OTP login
  preferred_lang  TEXT DEFAULT 'en',
  consent_given   BOOLEAN DEFAULT FALSE,
  consent_date    TIMESTAMPTZ,
  -- Saved profile fields (all optional, user controls what to save)
  saved_profile   JSONB DEFAULT '{}'::jsonb
);

-- ── Scheme matches table (Phase 3) ───────────────────────────────────────────
-- Stores which schemes a user matched, so they don't have to recheck
CREATE TABLE IF NOT EXISTS scheme_matches (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ DEFAULT now(),
  scheme_id   TEXT,
  eligible    BOOLEAN,
  reasons     JSONB
);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Users can only see their own data
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheme_matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own data" ON users
  FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users see own matches" ON scheme_matches
  FOR ALL USING (auth.uid() = user_id);
