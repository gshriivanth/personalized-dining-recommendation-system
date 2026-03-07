-- Schema for Personalized Dining Recommendation System

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
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    primary key (source, food_id)
);

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
    user_id uuid primary key references auth.users(id) on delete cascade,
    calories double precision,
    protein double precision,
    carbs double precision,
    fat double precision,
    fiber double precision,
    updated_at timestamptz default now()
);

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

create table if not exists user_favorites (
    user_id uuid not null references auth.users(id) on delete cascade,
    source text not null,
    food_id bigint not null,
    added_at timestamptz default now(),
    expires_at timestamptz,
    primary key (user_id, source, food_id),
    foreign key (source, food_id)
        references foods (source, food_id)
        on delete cascade
);

create table if not exists user_consumption_log (
    log_id bigserial primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    source text not null,
    food_id bigint not null,
    consumed_at timestamptz default now(),
    serving_size_g double precision default 100,
    calories double precision,
    protein double precision,
    carbs double precision,
    fat double precision,
    fiber double precision,
    foreign key (source, food_id)
        references foods (source, food_id)
        on delete cascade
);

create index if not exists idx_foods_name on foods (name);
create index if not exists idx_foods_brand on foods (brand);
create index if not exists idx_food_tags_tag on food_tags (tag);
create index if not exists idx_user_favorites_user on user_favorites (user_id);
create index if not exists idx_user_favorites_exp on user_favorites (expires_at);
create index if not exists idx_consumption_user_time on user_consumption_log (user_id, consumed_at desc);
