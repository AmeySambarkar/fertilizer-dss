import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from scripts.fetch_imd import summarize_imd

DATABASE_URL = "postgresql+psycopg2://fert_user:fert_pass@db:5432/fertdss"
engine = create_engine(DATABASE_URL)

app = FastAPI(title="Fertilizer DSS with IMD Integration")

class RecommendationRequest(BaseModel):
    field_id: str
    crop: str
    budget_inr: float

def featurize_field(field_id: str, crop: str):
    q = """
        SELECT f.lat, f.lon, f.area_ha, gs.season_year, gs.crop, gs.planting_date, gs.harvest_date,
               (gs.soil_snapshot->>'n_kg_ha')::float as soil_n,
               (gs.soil_snapshot->>'p_olsen_mg_kg')::float as soil_p,
               (gs.soil_snapshot->>'k_mg_kg')::float as soil_k,
               (gs.soil_snapshot->>'ph')::float as ph
        FROM field f
        JOIN growing_season gs ON f.id = gs.field_id
        WHERE f.id = %(field_id)s
        ORDER BY gs.season_year DESC
        LIMIT 1
    """
    df = pd.read_sql(q, engine, params={"field_id": field_id})
    if df.empty:
        raise ValueError(f"No field data found for {field_id}")

    lat, lon = df.iloc[0]["lat"], df.iloc[0]["lon"]
    planting_date = pd.to_datetime(df.iloc[0]["planting_date"]).strftime("%Y-%m-%d")
    harvest_date = pd.to_datetime(df.iloc[0]["harvest_date"]).strftime("%Y-%m-%d")

    # 🔗 Fetch live IMD-style weather data
    weather = summarize_imd(lat, lon, planting_date, harvest_date)

    df["total_rainfall"] = weather["total_rainfall_mm"]
    df["gdd"] = weather["gdd"]
    df["mean_temp"] = weather["mean_temp"]

    return df, df.to_dict(orient="records")[0]

@app.post("/recommendations/sync")
async def request_recommendation_sync(req: RecommendationRequest):
    try:
        X_df, X_dict = featurize_field(req.field_id, req.crop)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 🔮 Simulated recommendation
    rec = {
        "n_recommendation_kg_ha": 120,
        "p_recommendation_kg_ha": 60,
        "k_recommendation_kg_ha": 40,
    }

    return {
        "status": "ok",
        "weather": {
            "total_rainfall_mm": X_dict["total_rainfall"],
            "gdd": X_dict["gdd"],
            "mean_temp": X_dict["mean_temp"]
        },
        "recommendations": rec
    }
