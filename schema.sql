-- enable extensions (may require superuser inside some environments)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users
CREATE TABLE IF NOT EXISTS app_user (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  phone TEXT,
  email TEXT UNIQUE,
  role TEXT NOT NULL CHECK (role IN ('farmer','agronomist','admin')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Farms and Fields
CREATE TABLE IF NOT EXISTS farm (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
  name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS field (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  farm_id UUID REFERENCES farm(id) ON DELETE CASCADE,
  name TEXT,
  area_ha NUMERIC,
  geom GEOMETRY(POLYGON, 4326),
  centroid GEOMETRY(POINT, 4326),
  default_crop TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS field_geom_idx ON field USING GIST(geom);

-- Soil Sample
CREATE TABLE IF NOT EXISTS soil_sample (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  field_id UUID REFERENCES field(id) ON DELETE CASCADE,
  sample_date DATE,
  depth_cm INTEGER,
  n_kg_ha NUMERIC,
  p_olsen_mg_kg NUMERIC,
  k_mg_kg NUMERIC,
  ph NUMERIC,
  organic_carbon_pct NUMERIC,
  ec NUMERIC,
  cec NUMERIC,
  texture TEXT,
  lab_json JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- GrowingSeason (canonical training row)
CREATE TABLE IF NOT EXISTS growing_season (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  field_id UUID REFERENCES field(id) ON DELETE CASCADE,
  season_year INTEGER,
  crop TEXT,
  planting_date DATE,
  harvest_date DATE,
  previous_crop TEXT,
  soil_snapshot JSONB,
  weather_aggregates JSONB,
  rs_aggregates JSONB,
  fertilizer_history JSONB,
  final_yield_kg_ha NUMERIC,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_growing_season_field ON growing_season(field_id);

-- Weather record (optional)
CREATE TABLE IF NOT EXISTS weather_record (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  date DATE NOT NULL,
  location GEOMETRY(POINT, 4326),
  tmin NUMERIC,
  tmax NUMERIC,
  rainfall_mm NUMERIC,
  rh NUMERIC,
  solar_rad NUMERIC,
  raw_json JSONB
);

-- Remote sensing / NDVI
CREATE TABLE IF NOT EXISTS remote_sensing (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  date DATE,
  field_id UUID REFERENCES field(id) ON DELETE CASCADE,
  ndvi NUMERIC,
  lai NUMERIC,
  cloud_cover NUMERIC,
  raw_json JSONB
);

-- Application events
CREATE TABLE IF NOT EXISTS application_event (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  field_id UUID REFERENCES field(id) ON DELETE CASCADE,
  event_date DATE,
  type TEXT,
  fertilizer_json JSONB,
  notes TEXT
);

-- Recommendations
CREATE TABLE IF NOT EXISTS recommendation (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  field_id UUID REFERENCES field(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  requested_by UUID REFERENCES app_user(id),
  target_crop TEXT,
  recommended_json JSONB,
  status TEXT DEFAULT 'completed'
);
CREATE INDEX IF NOT EXISTS idx_recommendation_field ON recommendation(field_id);
