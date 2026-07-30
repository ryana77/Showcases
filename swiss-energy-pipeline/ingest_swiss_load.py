import os
import pandas as pd
from entsoe import EntsoePandasClient
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------------------------
ENTSOE_API_KEY = os.getenv("ENTSOE_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = "raw_swiss_energy"
COUNTRY_CODE = "CH"  # Switzerland
TIMEZONE = "Europe/Zurich"

# Swiss Interconnectors (Grid zones connected to Switzerland)
NEIGHBOR_COUNTRIES = ["DE_LU", "FR", "IT", "AT"]

if not ENTSOE_API_KEY or not GCP_PROJECT_ID:
    raise ValueError("Missing required environment variables (ENTSOE_API_KEY / GCP_PROJECT_ID)")

client_entsoe = EntsoePandasClient(api_key=ENTSOE_API_KEY)
client_bq = bigquery.Client(project=GCP_PROJECT_ID)

# Define date range (Yesterday midnight to today midnight local time)
now_swiss = pd.Timestamp.now(tz=TIMEZONE)
start_dt = (now_swiss - pd.Timedelta(days=1)).floor('D')
end_dt = now_swiss.floor('D')

print(f"--- Fetching ENTSO-E data for {start_dt.date()} ---")

# Helper function to run a BigQuery MERGE transaction
def run_bq_merge(df: pd.DataFrame, temp_table: str, merge_sql: str):
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    load_job = client_bq.load_table_from_dataframe(df, temp_table, job_config=job_config)
    load_job.result()
    query_job = client_bq.query(merge_sql)
    query_job.result()


# ------------------------------------------------------------------------------
# DATASET 1: ACTUAL & FORECAST LOAD
# ------------------------------------------------------------------------------
def process_load():
    print("Processing Grid Load...")
    actual = client_entsoe.query_load(COUNTRY_CODE, start=start_dt, end=end_dt)
    forecast = client_entsoe.query_load_forecast(COUNTRY_CODE, start=start_dt, end=end_dt)

    if isinstance(actual, pd.DataFrame): actual = actual.squeeze()
    if isinstance(forecast, pd.DataFrame): forecast = forecast.squeeze()

    # Join actual and forecasted load
    df = pd.concat([actual, forecast], axis=1)
    
    # 1. Force exact column names on the joined DataFrame
    df.columns = ['actual_load', 'forecasted_load']

    # 2. Reset index to move timestamp out of index into a column
    df = df.reset_index()
    
    # 3. Rename the timestamp column explicitly
    df.columns.values[0] = 'raw_timestamp'
    
    # 4. Standardize timestamps and add area_code
    df['raw_timestamp'] = pd.to_datetime(df['raw_timestamp'], utc=True)
    df['raw_timestamp'] = df['raw_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    df['area_code'] = COUNTRY_CODE

    # Ensure all column names are clean and lowercase
    df.columns = df.columns.str.lower()

    temp_table = f"{GCP_PROJECT_ID}.{DATASET_ID}.stg_temp_load"
    target_table = f"{GCP_PROJECT_ID}.{DATASET_ID}.raw_entsoe_load"
    
    sql = f"""
    MERGE INTO `{target_table}` T
    USING (
      SELECT 
        TIMESTAMP(raw_timestamp) AS timestamp_utc, 
        area_code,
        CAST(actual_load AS NUMERIC) AS actual_load_mw,
        CAST(forecasted_load AS NUMERIC) AS forecasted_load_mw
      FROM `{temp_table}`
    ) S ON T.timestamp_utc = S.timestamp_utc AND T.area_code = S.area_code
    WHEN MATCHED THEN 
      UPDATE SET 
        actual_load_mw = S.actual_load_mw, 
        forecasted_load_mw = S.forecasted_load_mw, 
        ingested_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN 
      INSERT (timestamp_utc, area_code, actual_load_mw, forecasted_load_mw, ingested_at)
      VALUES (S.timestamp_utc, S.area_code, S.actual_load_mw, S.forecasted_load_mw, CURRENT_TIMESTAMP());
    """
    run_bq_merge(df, temp_table, sql)
    print("✓ Load data merged successfully.")


# ------------------------------------------------------------------------------
# DATASET 2: GENERATION BY FUEL TYPE
# ------------------------------------------------------------------------------
def process_generation():
    print("Processing Generation Mix...")
    gen_df = client_entsoe.query_generation(COUNTRY_CODE, start=start_dt, end=end_dt)
    
    # Flatten multi-level column names if returned by entsoe-py
    if isinstance(gen_df.columns, pd.MultiIndex):
        gen_df = gen_df.xs('Actual Aggregated', axis=1, level=1, drop_level=True)

    # Move timestamp index to a regular column
    df_long = gen_df.reset_index()
    timestamp_col_name = df_long.columns[0]
    df_long.rename(columns={timestamp_col_name: 'raw_timestamp'}, inplace=True)

    # Melt dataframe from wide (fuel types as columns) to long format
    df_long = pd.melt(
        df_long, 
        id_vars=['raw_timestamp'], 
        var_name='production_type', 
        value_name='actual_generation_mw'
    )
    
    # FIX: Convert raw_timestamp explicitly to datetime before using .dt
    df_long['raw_timestamp'] = pd.to_datetime(df_long['raw_timestamp'], utc=True)
    df_long['raw_timestamp'] = df_long['raw_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    df_long['area_code'] = COUNTRY_CODE
    df_long.dropna(subset=['actual_generation_mw'], inplace=True)

    temp_table = f"{GCP_PROJECT_ID}.{DATASET_ID}.stg_temp_gen"
    target_table = f"{GCP_PROJECT_ID}.{DATASET_ID}.raw_entsoe_generation"

    sql = f"""
    MERGE INTO `{target_table}` T
    USING (
      SELECT 
        TIMESTAMP(raw_timestamp) AS timestamp_utc, 
        area_code, 
        production_type,
        CAST(actual_generation_mw AS NUMERIC) AS actual_generation_mw
      FROM `{temp_table}`
    ) S ON T.timestamp_utc = S.timestamp_utc AND T.area_code = S.area_code AND T.production_type = S.production_type
    WHEN MATCHED THEN 
      UPDATE SET 
        actual_generation_mw = S.actual_generation_mw, 
        ingested_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN 
      INSERT (timestamp_utc, area_code, production_type, actual_generation_mw, ingested_at)
      VALUES (S.timestamp_utc, S.area_code, S.production_type, S.actual_generation_mw, CURRENT_TIMESTAMP());
    """
    run_bq_merge(df_long, temp_table, sql)
    print("✓ Generation data merged successfully.")


# ------------------------------------------------------------------------------
# DATASET 3: CROSS-BORDER PHYSICAL FLOWS
# ------------------------------------------------------------------------------
def process_cross_border_flows():
    print("Processing Cross-Border Flows...")
    flow_records = []

    for neighbor in NEIGHBOR_COUNTRIES:
        # Imports to CH
        try:
            imports = client_entsoe.query_crossborder_flows(neighbor, COUNTRY_CODE, start=start_dt, end=end_dt)
            if isinstance(imports, pd.DataFrame): imports = imports.squeeze()
            for ts, val in imports.items():
                flow_records.append({'raw_timestamp': ts, 'out_area_code': neighbor, 'in_area_code': COUNTRY_CODE, 'flow_mw': val})
        except Exception as e:
            print(f"Warning: Could not fetch flows {neighbor} -> {COUNTRY_CODE}: {e}")

        # Exports from CH
        try:
            exports = client_entsoe.query_crossborder_flows(COUNTRY_CODE, neighbor, start=start_dt, end=end_dt)
            if isinstance(exports, pd.DataFrame): exports = exports.squeeze()
            for ts, val in exports.items():
                flow_records.append({'raw_timestamp': ts, 'out_area_code': COUNTRY_CODE, 'in_area_code': neighbor, 'flow_mw': val})
        except Exception as e:
            print(f"Warning: Could not fetch flows {COUNTRY_CODE} -> {neighbor}: {e}")

    df_flows = pd.DataFrame(flow_records)
    # Convert to datetime explicitly before using the .dt accessor
    df_flows['raw_timestamp'] = pd.to_datetime(df_flows['raw_timestamp'], utc=True)
    df_flows['raw_timestamp'] = df_flows['raw_timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    df_flows.dropna(subset=['flow_mw'], inplace=True)

    temp_table = f"{GCP_PROJECT_ID}.{DATASET_ID}.stg_temp_flows"
    target_table = f"{GCP_PROJECT_ID}.{DATASET_ID}.raw_entsoe_cross_border_flow"

    sql = f"""
    MERGE INTO `{target_table}` T
    USING (
      SELECT TIMESTAMP(raw_timestamp) AS timestamp_utc, out_area_code, in_area_code,
             CAST(flow_mw AS NUMERIC) AS flow_mw
      FROM `{temp_table}`
    ) S ON T.timestamp_utc = S.timestamp_utc AND T.out_area_code = S.out_area_code AND T.in_area_code = S.in_area_code
    WHEN MATCHED THEN UPDATE SET flow_mw = S.flow_mw, ingested_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT (timestamp_utc, out_area_code, in_area_code, flow_mw, ingested_at)
    VALUES (S.timestamp_utc, S.out_area_code, S.in_area_code, S.flow_mw, CURRENT_TIMESTAMP());
    """
    run_bq_merge(df_flows, temp_table, sql)
    print("✓ Cross-border flows merged successfully.")


if __name__ == "__main__":
    process_load()
    process_generation()
    process_cross_border_flows()
