import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor
import joblib
import pathlib

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fert_user:fert_pass@localhost:5432/fertdss")
engine = create_engine(DATABASE_URL)

def load_growing_season():
    q = text("""
        SELECT id, field_id, season_year, crop, planting_date, harvest_date,
               final_yield_kg_ha,
               (soil_snapshot->>'n_kg_ha')::float as soil_n,
               (soil_snapshot->>'p_olsen_mg_kg')::float as soil_p,
               (soil_snapshot->>'k_mg_kg')::float as soil_k,
               (soil_snapshot->>'ph')::float as ph,
               (weather_aggregates->>'total_rainfall_mm')::float as total_rainfall,
               (weather_aggregates->>'gdd')::float as gdd,
               (rs_aggregates->>'mean_ndvi')::float as mean_ndvi
        FROM growing_season
    """)
    df = pd.read_sql(q, engine)
    df = df.dropna(subset=['final_yield_kg_ha'])
    return df

def featurize(df):
    X = df[['soil_n','soil_p','soil_k','ph','total_rainfall','gdd','mean_ndvi']].fillna(0)
    X = pd.concat([X, pd.get_dummies(df['crop'], prefix='crop')], axis=1)
    y = df['final_yield_kg_ha']
    return X, y

def train_and_save(X, y):
    if X.shape[0] < 10:
        print(f"Not enough rows to train a reliable model (found {X.shape[0]}). Add more data.")
        return
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)
    model = XGBRegressor(n_estimators=100, max_depth=5, random_state=42, verbosity=0)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    rmse = mean_squared_error(y_test, preds, squared=False)
    print(f"Test RMSE: {rmse:.2f}")
    models_dir = pathlib.Path("models")
    models_dir.mkdir(exist_ok=True)
    joblib.dump(model, models_dir / "xgb_baseline.joblib")
    print("Saved model to models/xgb_baseline.joblib")

def main():
    df = load_growing_season()
    if df.shape[0] == 0:
        print("No growing_season rows found - run seed script first.")
        return
    X, y = featurize(df)
    train_and_save(X,y)

if __name__ == '__main__':
    main()
