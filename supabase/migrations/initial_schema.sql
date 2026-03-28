-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Drop existing tables to ensure clean schema (WARNING: This deletes data)
drop table if exists attendance cascade;
drop table if exists session_tokens cascade;
drop table if exists sessions cascade;
drop table if exists students cascade;
drop table if exists teachers cascade;

-- Students table (Public Profile)
-- Linked to auth.users via id
create table if not exists students (
  id uuid primary key references auth.users(id) on delete cascade,
  student_id text unique not null,
  name text not null,
  class text not null,
  created_at timestamp with time zone default now()
);

-- Teachers table (Public Profile)
-- Linked to auth.users via id
create table if not exists teachers (
  id uuid primary key references auth.users(id) on delete cascade,
  teacher_id text unique not null,
  name text not null,
  subject text not null,
  created_at timestamp with time zone default now()
);

-- Sessions table
create table if not exists sessions (
  id uuid primary key default uuid_generate_v4(),
  teacher_id uuid references teachers(id) on delete cascade,
  subject text not null,
  class text not null,
  start_time timestamp with time zone default now(),
  is_active boolean default true,
  created_at timestamp with time zone default now()
);

-- Session Tokens (for rotating QR)
create table if not exists session_tokens (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid references sessions(id) on delete cascade,
  token text not null,
  expires_at timestamp with time zone not null,
  created_at timestamp with time zone default now()
);

-- Attendance table
create table if not exists attendance (
  id uuid primary key default uuid_generate_v4(),
  student_id uuid references students(id) on delete cascade,
  session_id uuid references sessions(id) on delete cascade,
  timestamp timestamp with time zone default now(),
  status text default 'present',
  unique(student_id, session_id)
);

-- ─── Security Policies (Optional but Recommended) ───

-- Enable RLS
alter table students enable row level security;
alter table teachers enable row level security;
alter table sessions enable row level security;
alter table attendance enable row level security;

-- Simple policy: authenticated users can read, but only specific roles can write (handled by backend)
create policy "Public profiles are viewable by everyone" on students for select using (true);
create policy "Public profiles are viewable by everyone" on teachers for select using (true);
