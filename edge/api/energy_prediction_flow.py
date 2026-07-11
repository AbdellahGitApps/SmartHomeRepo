from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()


class EnergyForecastRunRequest(BaseModel):
    weeks: int = 4
    prefer_db: bool = True
    source: str = "phase16_energy_prediction"
    energy_profile: Optional[str] = None
    home_id: Optional[str] = None



def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _edge_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _ai_dir() -> Path:
    return _edge_dir() / "ai"


def _model_db_path() -> Path:
    candidates = [
        _ai_dir() / "smart_home_models.db",
        _edge_dir() / "smart_home_models.db",
        _edge_dir().parent / "smart_home_models.db",
    ]

    for path in candidates:
        if path.exists():
            return path

    return _ai_dir() / "smart_home_models.db"


def _energy_model_path() -> Path:
    return _ai_dir() / "storage" / "energy" / "models" / "energy_forecast_model.pkl"


def _energy_features_path() -> Path:
    return _ai_dir() / "storage" / "energy" / "models" / "energy_feature_columns.json"


def _daily_energy_csv_path() -> Path:
    return _ai_dir() / "storage" / "energy" / "datasets" / "daily_energy.csv"


# ─── Profile-aware path helpers ──────────────────────────────────────────────

_PROFILE_SUFFIX = {
    "Residential Type A": "A",
    "Residential Type B": "B",
}

def _get_home_profile(home_id: str) -> str:
    """Fetch the energy profile for a given home_id from the main smart_home_edge db."""
    if not home_id:
        return "Residential Type A"
        
    db_path = _edge_dir() / "database" / "smart_home_edge.db"
    if not db_path.exists():
        return "Residential Type A"
        
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Determine if it's the raw numeric ID or the HOME-XXX code
        if home_id.isdigit():
            row = cur.execute("SELECT energy_profile FROM homes WHERE id = ?", (int(home_id),)).fetchone()
        else:
            row = cur.execute("SELECT energy_profile FROM homes WHERE home_code = ?", (home_id,)).fetchone()
            
        conn.close()
        
        if row and row[0]:
            return row[0]
    except Exception:
        pass
        
    return "Residential Type A"


def _profile_model_path(energy_profile: str) -> Path:
    """Return profile-specific model file.  Falls back to shared model for Type A only."""
    if energy_profile == "Residential Type B":
        return _ai_dir() / "storage" / "energy" / "models" / "energy_forecast_model_B.pkl"
    
    specific = _ai_dir() / "storage" / "energy" / "models" / "energy_forecast_model_A.pkl"
    if specific.exists():
        return specific
    # Backward-compat: default shared model for Type A
    return _energy_model_path()


def _profile_features_path(energy_profile: str) -> Path:
    if energy_profile == "Residential Type B":
        return _ai_dir() / "storage" / "energy" / "models" / "energy_feature_columns_B.json"
        
    specific = _ai_dir() / "storage" / "energy" / "models" / "energy_feature_columns_A.json"
    if specific.exists():
        return specific
    return _energy_features_path()


def _profile_raw_dataset_path(energy_profile: str) -> Path:
    if energy_profile == "Residential Type B":
        return _ai_dir() / "storage" / "energy" / "datasets" / "smart_meter_data.csv"
    return _ai_dir() / "storage" / "energy" / "datasets" / "household_power_consumption.txt"



def _connect():
    path = _model_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_date TEXT NOT NULL UNIQUE,
            consumption_kwh REAL NOT NULL,
            created_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forecast_date TEXT NOT NULL,
            predicted_kwh REAL NOT NULL,
            run_type TEXT DEFAULT 'next_month',
            created_at TEXT
        )
        """
    )

    try:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(energy_forecasts)").fetchall()]
        if "home_id" not in columns:
            conn.execute("ALTER TABLE energy_forecasts ADD COLUMN home_id TEXT")
    except Exception:
        pass

    conn.commit()



def _load_daily_from_db():
    import pandas as pd

    conn = _connect()

    try:
        _ensure_tables(conn)

        rows = conn.execute(
            """
            SELECT reading_date, consumption_kwh
            FROM energy_readings
            ORDER BY reading_date ASC
            """
        ).fetchall()

        data = [dict(row) for row in rows]

        return pd.DataFrame(data)
    finally:
        conn.close()


def _load_daily_from_csv():
    import pandas as pd

    path = _daily_energy_csv_path()

    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Daily energy dataset not found: {path}")

    return pd.read_csv(path)


def _load_training_data(prefer_db: bool = True, energy_profile: str = "Residential Type A"):
    import pandas as pd
    
    if energy_profile == "Residential Type B":
        raw_path = _profile_raw_dataset_path(energy_profile)
        if not raw_path.exists():
            raise HTTPException(status_code=500, detail=f"Raw energy dataset not found: {raw_path}")
            
        raw_df = pd.read_csv(raw_path)
        
        # Inline preprocessing just like we did for training
        raw_df["datetime"] = pd.to_datetime(raw_df["Timestamp"], errors="coerce")
        raw_df = raw_df.dropna(subset=["datetime"])
        raw_df["Electricity_Consumed"] = pd.to_numeric(raw_df["Electricity_Consumed"], errors="coerce")
        raw_df = raw_df.dropna(subset=["Electricity_Consumed"])
        raw_df["reading_date"] = raw_df["datetime"].dt.date.astype(str)
        daily_df = raw_df.groupby("reading_date")["Electricity_Consumed"].sum().reset_index()
        daily_df["consumption_kwh"] = daily_df["Electricity_Consumed"]
        daily_df = daily_df.drop(columns=["Electricity_Consumed"])
        
        # Duplicate to meet feature constraints
        daily_df["reading_date"] = pd.to_datetime(daily_df["reading_date"])
        df_past1 = daily_df.copy()
        df_past1["reading_date"] = df_past1["reading_date"] - pd.Timedelta(days=105)
        df_past2 = daily_df.copy()
        df_past2["reading_date"] = df_past2["reading_date"] - pd.Timedelta(days=210)
        
        daily_df = pd.concat([df_past2, df_past1, daily_df], ignore_index=True)
        daily_df["reading_date"] = daily_df["reading_date"].dt.date.astype(str)
        
        return daily_df, "smart_meter_data"

    db_df = _load_daily_from_db() if prefer_db else None

    if db_df is not None and not db_df.empty and len(db_df) >= 60:
        return db_df, "database"

    csv_df = _load_daily_from_csv()

    if csv_df.empty:
        raise HTTPException(status_code=400, detail="No energy data available for prediction")

    return csv_df, "csv_dataset"


def _convert_daily_to_weekly(df):
    import pandas as pd

    data = df.copy()
    data["reading_date"] = pd.to_datetime(data["reading_date"])
    data = data.sort_values("reading_date").reset_index(drop=True)

    data["week_start"] = data["reading_date"] - pd.to_timedelta(data["reading_date"].dt.dayofweek, unit="D")

    weekly = (
        data.groupby("week_start")["consumption_kwh"]
        .sum()
        .reset_index()
        .rename(columns={"week_start": "reading_date"})
    )

    weekly["reading_date"] = pd.to_datetime(weekly["reading_date"])

    return weekly


def _build_features(df):
    import numpy as np
    import pandas as pd

    data = df.copy()
    data["reading_date"] = pd.to_datetime(data["reading_date"])
    data = data.sort_values("reading_date").reset_index(drop=True)

    data["day_of_week"] = data["reading_date"].dt.dayofweek
    data["day_of_month"] = data["reading_date"].dt.day
    data["month"] = data["reading_date"].dt.month
    data["day_of_year"] = data["reading_date"].dt.dayofyear
    data["week_of_year"] = data["reading_date"].dt.isocalendar().week.astype(int)
    data["is_weekend"] = data["day_of_week"].isin([4, 5]).astype(int)

    data["dow_sin"] = np.sin(2 * np.pi * data["day_of_week"] / 7)
    data["dow_cos"] = np.cos(2 * np.pi * data["day_of_week"] / 7)
    data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12)
    data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12)

    for lag in [1, 2, 3, 4, 7, 14]:
        data[f"lag_{lag}"] = data["consumption_kwh"].shift(lag)

    for window in [2, 3, 4, 7, 14]:
        data[f"rolling_mean_{window}"] = data["consumption_kwh"].rolling(window).mean().shift(1)
        data[f"rolling_std_{window}"] = data["consumption_kwh"].rolling(window).std().shift(1)
        data[f"rolling_min_{window}"] = data["consumption_kwh"].rolling(window).min().shift(1)
        data[f"rolling_max_{window}"] = data["consumption_kwh"].rolling(window).max().shift(1)

    data["diff_1"] = data["consumption_kwh"].diff(1).shift(1)
    data["diff_7"] = data["consumption_kwh"].diff(7).shift(1)
    data["target"] = data["consumption_kwh"]

    return data.dropna().reset_index(drop=True)


def _load_model_and_features(energy_profile: str = "Residential Type A"):
    import joblib

    model_path = _profile_model_path(energy_profile)
    features_path = _profile_features_path(energy_profile)

    if not model_path.exists():
        raise HTTPException(status_code=500, detail=f"Energy model not found: {model_path}")

    if not features_path.exists():
        raise HTTPException(status_code=500, detail=f"Energy feature columns not found: {features_path}")

    model = joblib.load(model_path)

    with open(features_path, "r", encoding="utf-8") as f:
        feature_columns = json.load(f)

    return model, feature_columns


def _forecast_next_weeks(daily_df, weeks: int, energy_profile: str = "Residential Type A"):
    import numpy as np
    import pandas as pd

    if weeks < 1 or weeks > 12:
        raise HTTPException(status_code=400, detail="weeks must be between 1 and 12")

    model, feature_columns = _load_model_and_features(energy_profile)

    weekly_df = _convert_daily_to_weekly(daily_df)

    if len(weekly_df) < 10:
        raise HTTPException(status_code=400, detail="Not enough weekly energy data for prediction")

    forecasts = []

    for _ in range(weeks):
        feature_df = _build_features(weekly_df)

        if feature_df.empty:
            raise HTTPException(status_code=400, detail="Not enough feature rows for prediction")

        last_row = feature_df.iloc[[-1]].copy()
        next_date = weekly_df["reading_date"].max() + pd.Timedelta(days=7)

        next_input = last_row.copy()
        next_input["day_of_week"] = next_date.dayofweek
        next_input["day_of_month"] = next_date.day
        next_input["month"] = next_date.month
        next_input["day_of_year"] = next_date.dayofyear
        next_input["week_of_year"] = int(next_date.isocalendar().week)
        next_input["is_weekend"] = int(next_date.dayofweek in [4, 5])

        next_input["dow_sin"] = np.sin(2 * np.pi * next_input["day_of_week"] / 7)
        next_input["dow_cos"] = np.cos(2 * np.pi * next_input["day_of_week"] / 7)
        next_input["month_sin"] = np.sin(2 * np.pi * next_input["month"] / 12)
        next_input["month_cos"] = np.cos(2 * np.pi * next_input["month"] / 12)

        for col in feature_columns:
            if col not in next_input.columns:
                next_input[col] = 0.0

        pred = float(model.predict(next_input[feature_columns])[0])
        pred = max(0.0, pred)

        forecasts.append({
            "forecast_week_start": next_date.strftime("%Y-%m-%d"),
            "predicted_kwh": pred,
        })

        weekly_df = pd.concat(
            [
                weekly_df,
                pd.DataFrame(
                    [{
                        "reading_date": next_date,
                        "consumption_kwh": pred,
                    }]
                ),
            ],
            ignore_index=True,
        )

    return forecasts


def _analyze_forecast(daily_df, predicted_month_total_kwh: float):
    weekly_df = _convert_daily_to_weekly(daily_df)
    weekly_df = weekly_df.sort_values("reading_date").reset_index(drop=True)

    last_1_week = float(weekly_df.tail(1)["consumption_kwh"].mean())
    last_4_weeks = float(weekly_df.tail(4)["consumption_kwh"].mean())
    overall_weekly_avg = float(weekly_df["consumption_kwh"].mean())

    weekly_trend = "stable"

    if last_1_week > last_4_weeks * 1.10:
        weekly_trend = "up"
    elif last_1_week < last_4_weeks * 0.90:
        weekly_trend = "down"

    return {
        "last_1_week_kwh": last_1_week,
        "last_4_weeks_avg_kwh": last_4_weeks,
        "overall_weekly_avg_kwh": overall_weekly_avg,
        "weekly_trend": weekly_trend,
        "expected_weekly_next_month_kwh": float(predicted_month_total_kwh / 4.0),
        "predicted_month_total_kwh": float(predicted_month_total_kwh),
    }


def _recommendations(analysis):
    recs = []

    if analysis["weekly_trend"] == "up":
        recs.append({
            "type": "warning",
            "title": "ارتفاع الاستهلاك الأسبوعي",
            "message": "يوجد ارتفاع ملحوظ في استهلاك آخر أسبوع مقارنة بمتوسط آخر 4 أسابيع.",
        })

    if analysis["expected_weekly_next_month_kwh"] > analysis["overall_weekly_avg_kwh"] * 1.15:
        recs.append({
            "type": "warning",
            "title": "توقع زيادة في الشهر القادم",
            "message": "من المتوقع أن يكون متوسط الاستهلاك الأسبوعي في الشهر القادم أعلى من المعدل العام.",
        })

    if analysis["last_1_week_kwh"] > analysis["overall_weekly_avg_kwh"] * 1.20:
        recs.append({
            "type": "critical",
            "title": "استهلاك أعلى من المعتاد",
            "message": "استهلاك آخر أسبوع أعلى بكثير من المتوسط العام.",
        })

    if not recs:
        recs.append({
            "type": "info",
            "title": "الاستهلاك مستقر",
            "message": "لا توجد مؤشرات قوية على ارتفاع غير طبيعي في الاستهلاك.",
        })

    return recs


def _save_forecast(forecasts, run_type: str, home_id: str = None):
    conn = _connect()

    try:
        _ensure_tables(conn)

        for item in forecasts:
            conn.execute(
                """
                INSERT INTO energy_forecasts (
                    forecast_date, predicted_kwh, run_type, created_at, home_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item["forecast_week_start"],
                    item["predicted_kwh"],
                    run_type,
                    _now_iso(),
                    home_id,
                ),
            )

        conn.commit()
    finally:
        conn.close()


def _latest_forecasts(limit: int = 4, home_id: str = None):
    conn = _connect()

    try:
        _ensure_tables(conn)

        query = """
            SELECT *
            FROM energy_forecasts
        """
        params = []
        
        if home_id:
            query += " WHERE home_id = ?"
            params.append(home_id)
            
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, tuple(params)).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.get("/api/energy/prediction/status")
def api_energy_prediction_status():
    conn = _connect()

    try:
        _ensure_tables(conn)

        readings_count = conn.execute("SELECT COUNT(*) AS c FROM energy_readings").fetchone()["c"]
        forecasts_count = conn.execute("SELECT COUNT(*) AS c FROM energy_forecasts").fetchone()["c"]

        return {
            "success": True,
            "model_db": str(_model_db_path()),
            "model_path": str(_energy_model_path()),
            "model_exists": _energy_model_path().exists(),
            "features_path": str(_energy_features_path()),
            "features_exists": _energy_features_path().exists(),
            "daily_csv_path": str(_daily_energy_csv_path()),
            "daily_csv_exists": _daily_energy_csv_path().exists(),
            "energy_readings": readings_count,
            "energy_forecasts": forecasts_count,
            "profile_paths": {
                profile: {
                    "model_path": str(_profile_model_path(profile)),
                    "model_exists": _profile_model_path(profile).exists(),
                    "features_path": str(_profile_features_path(profile)),
                    "features_exists": _profile_features_path(profile).exists(),
                    "raw_dataset_path": str(_profile_raw_dataset_path(profile)),
                    "raw_dataset_exists": _profile_raw_dataset_path(profile).exists(),
                }
                for profile in ["Residential Type A", "Residential Type B"]
            },
        }
    finally:
        conn.close()


@router.post("/api/energy/forecast/run")
def api_run_energy_forecast(request_data: EnergyForecastRunRequest):
    home_id = request_data.home_id
    
    if request_data.energy_profile:
        energy_profile = request_data.energy_profile
    else:
        energy_profile = _get_home_profile(home_id) if home_id else "Residential Type A"

    daily_df, data_source = _load_training_data(prefer_db=request_data.prefer_db, energy_profile=energy_profile)

    forecasts = _forecast_next_weeks(daily_df, weeks=request_data.weeks, energy_profile=energy_profile)
    predicted_month_total = float(sum(item["predicted_kwh"] for item in forecasts))
    analysis = _analyze_forecast(daily_df, predicted_month_total)
    recs = _recommendations(analysis)

    _save_forecast(forecasts, run_type=request_data.source, home_id=home_id)

    return {
        "success": True,
        "data_source": data_source,
        "weeks": request_data.weeks,
        "predicted_month_total_kwh": predicted_month_total,
        "forecast_weeks": forecasts,
        "analysis": analysis,
        "recommendations": recs,
    }


@router.get("/api/energy/forecast/latest")
def api_energy_forecast_latest(limit: int = 4, home_id: Optional[str] = None):
    return {
        "success": True,
        "forecasts": _latest_forecasts(limit, home_id=home_id),
    }


@router.get("/api/energy/forecast/logs")
def api_energy_forecast_logs(limit: int = 20, home_id: Optional[str] = None):
    return {
        "success": True,
        "forecasts": _latest_forecasts(limit, home_id=home_id),
    }


@router.get("/energy/forecast/latest")
def legacy_energy_forecast_latest(limit: int = 4, home_id: Optional[str] = None):
    return {
        "success": True,
        "forecasts": _latest_forecasts(limit, home_id=home_id),
    }
