-- Ejecutar una vez en el SQL Editor de Neon
create table if not exists tasks (
  id serial primary key,
  user_id text not null,
  title text not null,
  done boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists tasks_user_id_idx on tasks (user_id);
