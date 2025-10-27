import os
import uuid
import psycopg2
import psycopg2.extras as pg_extras
import pandas as pd

def connect_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        database=os.environ.get("DB_NAME", "fertdss"),
        user=os.environ.get("DB_USER", "fert_user"),
        password=os.environ.get("DB_PASSWORD", "fert_pass")
    )

def insert_fields(conn, df):
    cur = conn.cursor()
    cur.execute("DELETE FROM field;")
    conn.commit()
    for _, r in df.iterrows():
        field_id = str(uuid.uuid4())
        lat = float(r['lat'])
        lon = float(r['lon'])
        delta = 0.0008
        polygon_wkt = f"POLYGON(({lon-delta} {lat-delta},{lon+delta} {lat-delta},{lon+delta} {lat+delta},{lon-delta} {lat+delta},{lon-delta} {lat-delta}))"
        centroid_wkt = f"POINT({lon} {lat})"
        cur.execute("""
            INSERT INTO field (id, name, area_ha, soil_type, geom, centroid)
            VALUES (%s, %s, %s, %s, ST_GeomFromText(%s,4326), ST_GeomFromText(%s,4326))
        """, (field_id, r['name'], float(r['area_ha']), r['soil_type'], polygon_wkt, centroid_wkt))
    conn.commit()
    cur.close()

def insert_growing_season(conn, df):
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM field;")
    mapping = {row[1]: row[0] for row in cur.fetchall()}
    for _, r in df.iterrows():
        field_id = mapping.get(r['field_name'])
        if not field_id:
            print(f"⚠️ Skipping {r['field_name']} (not found in DB)")
            continue
        soil_snapshot = {
            'n_kg_ha': float(r['soil_n']),
            'p_olsen_mg_kg': float(r['soil_p']),
            'k_mg_kg': float(r['soil_k']),
            'ph': float(r['ph'])
        }
        weather = {'total_rainfall_mm': float(r['rainfall_mm']), 'gdd': float(r['gdd'])}
        rs = {'mean_ndvi': float(r['mean_ndvi'])}
        cur.execute("""
            INSERT INTO growing_season
            (id, field_id, season_year, crop, planting_date, harvest_date, previous_crop,
             soil_snapshot, weather_aggregates, rs_aggregates, final_yield_kg_ha)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            str(uuid.uuid4()), field_id, int(r['season_year']), r['crop'],
            r['planting_date'], r['harvest_date'], r['previous_crop'],
            pg_extras.Json(soil_snapshot), pg_extras.Json(weather),
            pg_extras.Json(rs), float(r['final_yield_kg_ha'])
        ))
    conn.commit()
    cur.close()

def main():
    conn = connect_db()
    fields = pd.read_csv('/app/scripts/sample_fields.csv')
    gs = pd.read_csv('/app/scripts/sample_growing_season.csv')
    insert_fields(conn, fields)
    insert_growing_season(conn, gs)
    conn.close()
    print("✅ Database seeding complete.")

if __name__ == "__main__":
    main()
