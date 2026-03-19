-- Schema for Personalized Dining Recommendation System
-- Apply with: python scripts/init_db.py (from backend/)
--
-- NOTE: auth.users is managed entirely by Supabase Auth.
-- You must enable Email/Password sign-in in the Supabase dashboard
-- (Authentication -> Providers -> Email) before using user-facing endpoints.

-- ---------------------------------------------------------------------------
-- User profiles (extends auth.users; row created by trigger on sign-up)
-- ---------------------------------------------------------------------------

create table if not exists profiles (
    user_id    uuid primary key references auth.users(id) on delete cascade,
    name       text not null default '',
    created_at timestamptz not null default now()
);

-- Trigger: automatically create a profiles row when a new auth user signs up.
create or replace function handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (user_id, name)
  values (new.id, coalesce(new.raw_user_meta_data->>'name', ''))
  on conflict (user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();

alter table profiles enable row level security;
drop policy if exists "profiles: own row" on profiles;
create policy "profiles: own row" on profiles
  for all using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Foods (USDA + UCI dining)
-- ---------------------------------------------------------------------------

create table if not exists foods (
    source text not null,
    food_id bigint not null,
    name text not null,
    brand text,
    meal_category text default 'any',
    calories double precision,
    protein double precision,
    carbs double precision,
    fat double precision,
    fiber double precision,
    saturated_fat double precision,
    trans_fat double precision,
    cholesterol double precision,
    sodium double precision,
    sugars double precision,
    added_sugars double precision,
    vitamin_d double precision,
    calcium double precision,
    iron double precision,
    potassium double precision,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    primary key (source, food_id)
);

-- Migrations: add extended nutrition columns to existing tables.
alter table foods add column if not exists saturated_fat double precision;
alter table foods add column if not exists trans_fat double precision;
alter table foods add column if not exists cholesterol double precision;
alter table foods add column if not exists sodium double precision;
alter table foods add column if not exists sugars double precision;
alter table foods add column if not exists added_sugars double precision;
alter table foods add column if not exists vitamin_d double precision;
alter table foods add column if not exists calcium double precision;
alter table foods add column if not exists iron double precision;
alter table foods add column if not exists potassium double precision;

create table if not exists food_tags (
    source text not null,
    food_id bigint not null,
    tag text not null,
    created_at timestamptz default now(),
    primary key (source, food_id, tag),
    foreign key (source, food_id)
        references foods (source, food_id)
        on delete cascade
);

create table if not exists user_goals (
    user_id    uuid primary key references profiles(user_id) on delete cascade,
    calories   double precision,
    protein    double precision,
    carbs      double precision,
    fat        double precision,
    fiber      double precision,
    updated_at timestamptz not null default now()
);

alter table user_goals enable row level security;
drop policy if exists "user_goals: own row" on user_goals;
create policy "user_goals: own row" on user_goals
  for all using (auth.uid() = user_id);

create table if not exists user_recipes (
    recipe_id bigserial primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    calories double precision,
    protein double precision,
    carbs double precision,
    fat double precision,
    fiber double precision,
    tags text[] default '{}',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- user_favorites stores a snapshot of the food name so favorites are
-- displayable even when the dining item is not in the DB or cache.
-- There is intentionally NO foreign key to (foods.source, foods.food_id)
-- because UCI dining items are served from the in-memory cache, not stored
-- in the foods table, so an FK would prevent users from favoriting them.
create table if not exists user_favorites (
    user_id   uuid        not null references profiles(user_id) on delete cascade,
    source    text        not null,
    food_id   bigint      not null,
    food_name text        not null default '',
    added_at  timestamptz not null default now(),
    primary key (user_id, source, food_id)
);

-- Migration: add food_name if the table was created before it was added.
alter table user_favorites add column if not exists food_name text not null default '';

-- Migration: drop the FK to foods if it was mistakenly added in an earlier schema
-- version. UCI dining items are in-memory only and are never inserted into the
-- foods table, so this constraint blocks favoriting any dining-hall food.
do $$ begin
  if exists (
    select 1 from information_schema.table_constraints
    where table_name = 'user_favorites'
      and constraint_name = 'user_favorites_source_food_id_fkey'
  ) then
    alter table user_favorites drop constraint user_favorites_source_food_id_fkey;
  end if;
end $$;

alter table user_favorites enable row level security;
drop policy if exists "user_favorites: own rows" on user_favorites;
create policy "user_favorites: own rows" on user_favorites
  for all using (auth.uid() = user_id);

-- meal_type added to track which meal period the food was consumed in.
-- food_name snapshot stored so the log remains readable even after food is purged.
-- No FK to foods table (same reason as user_favorites).
create table if not exists user_consumption_log (
    log_id         uuid        primary key default gen_random_uuid(),
    user_id        uuid        not null references profiles(user_id) on delete cascade,
    source         text        not null,
    food_id        bigint      not null,
    food_name      text        not null default '',
    serving_size_g double precision not null default 100,
    calories       double precision,
    protein        double precision,
    carbs          double precision,
    fat            double precision,
    fiber          double precision,
    meal_type      text,
    consumed_at    timestamptz not null default now()
);

-- Migration: add food_name and meal_type if the table was created before they were added.
alter table user_consumption_log add column if not exists food_name text not null default '';
alter table user_consumption_log add column if not exists meal_type text;

-- Migration: drop the FK to foods if it was mistakenly added in an earlier schema
-- version. UCI dining items are in-memory only and are never inserted into the
-- foods table, so this constraint blocks logging any dining-hall food.
do $$ begin
  if exists (
    select 1 from information_schema.table_constraints
    where table_name = 'user_consumption_log'
      and constraint_name = 'user_consumption_log_source_food_id_fkey'
  ) then
    alter table user_consumption_log drop constraint user_consumption_log_source_food_id_fkey;
  end if;
end $$;

alter table user_consumption_log enable row level security;
drop policy if exists "consumption_log: own rows" on user_consumption_log;
create policy "consumption_log: own rows" on user_consumption_log
  for all using (auth.uid() = user_id);

create index if not exists idx_foods_name on foods (name);
create index if not exists idx_foods_brand on foods (brand);
create index if not exists idx_foods_updated_at on foods (updated_at);
create index if not exists idx_food_tags_tag on food_tags (tag);
create index if not exists idx_user_favorites_user on user_favorites (user_id);
create index if not exists idx_consumption_user_time on user_consumption_log (user_id, consumed_at desc);

-- ---------------------------------------------------------------------------
-- USDA food TTL: delete non-dining foods not refreshed in 30+ days.
-- Called at API startup (api/main.py lifespan) and nightly via pg_cron.
-- ---------------------------------------------------------------------------

create or replace function delete_stale_usda_foods(days_old int default 30)
returns int language plpgsql as $$
declare
  deleted_count int;
begin
  delete from foods
  where source not like 'uci_dining_%'
    and updated_at < now() - (days_old || ' days')::interval;
  get diagnostics deleted_count = row_count;
  return deleted_count;
end;
$$;

-- pg_cron: runs nightly at 03:00 UTC. Safe to re-run (unschedules first if exists).
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'purge-stale-foods') THEN
    PERFORM cron.unschedule('purge-stale-foods');
  END IF;
  PERFORM cron.schedule('purge-stale-foods', '0 3 * * *', 'select delete_stale_usda_foods(30)');
END;
$$;
