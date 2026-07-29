import os
import datetime
import pandas as pd
from entsoe import EntsoePandasClient
from google.cloud import bigquery

# ------------------------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------------------------
# 1. Fetch values from environment variables
ENTSOE_API_KEY = os.getenv("ENTSOE_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Safety checks to fail early if variables are missing
if not ENTSOE_API_KEY:
    raise ValueError("Missing ENTSOE_API_KEY environment variable!")
if not GCP_PROJECT_ID:
    raise ValueError("Missing GCP_PROJECT_ID environment variable!")

# 2. Use the secrets in your client initializations
entsoe_client = EntsoePandasClient(api_key=ENTSOE_API_KEY)

# BigQuery automatically finds the authentication credentials set by GitHub Actions
bq_client = bigquery.Client(project=GCP_PROJECT_ID)

DATASET_ID = "raw_swiss_energy"               # Dataset created in step 1
TARGET_TABLE = f"{GCP_PROJECT_ID}.{DATASET_ID}.raw_entsoe_load"
TEMP_STAGING_TABLE = f"{GCP_PROJECT_ID}.{DATASET_ID}.stg_temp_api_load"

COUNTRY_CODE = "CH"  # Switzerland Grid Area Code
TIMEZONE = "Europe/Zurich"

if not ENTSOE_API_KEY:
    raise ValueError("Missing ENTSOE_API_KEY environment variable.")

# ------------------------------------------------------------------------------
# 2. FETCH DATA FROM ENTSO-E API
# ------------------------------------------------------------------------------
def fetch_entsoe_data():
    """Fetches yesterday's actual and forecasted grid load for Switzerland."""
    client = EntsoePandasClient(api_key=ENTSOE_API_KEY)
    
    # Define date range (Yesterday midnight to today midnight in Swiss local time)
    now_swiss = pd.Timestamp.now(tz=TIMEZONE)
    start = (now_swiss - pd.Timedelta(days=1)).floor('D')
    end = now_swiss.floor('D')

    print(f"Fetching ENTSO-E data for {COUNTRY_CODE} from {start} to {end}...")

    # Query API (Returns Pandas Series indexed by UTC timestamp)
    actual_load = client.query_load(COUNTRY_CODE, start=start, end=end)
    forecast_load = client.query_load_forecast(COUNTRY_CODE, start=start, end=end)

    # Combine into a single DataFrame
    df = pd.DataFrame({
        'actual_load': actual_load,
        'forecasted_load': forecast_load
    }).reset_index()

    # Rename index column to raw_timestamp
    df.rename(columns={df.columns[0]: 'raw_timestamp'}, inplace=True)
    df['area_code'] = COUNTRY_CODE

    # Convert pandas Timestamp to ISO string format for BigQuery ingestion
    df['raw_timestamp'] = df['raw_timestamp'].dt.tz_convert('UTC').dt.strftime('%Y-%m-%d %H:%M:%S UTC')

    print(f"Retrieved {len(df)} hourly records.")
    return df

# ------------------------------------------------------------------------------
# 3. IDEMPOTENT LOAD INTO BIGQUERY (STAGING -> MERGE)
# ------------------------------------------------------------------------------
def load_to_bigquery(df: pd.DataFrame):
    """Loads DataFrame into a temp BigQuery table and runs an atomic MERGE."""
    bq_client = bigquery.Client(project=GCP_PROJECT_ID)

    # Step A: Write data to temporary staging table (truncates existing temp table)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    print(f"Writing payload to temporary table: {TEMP_STAGING_TABLE}...")
    load_job = bq_client.load_table_from_dataframe(
        df, TEMP_STAGING_TABLE, job_config=job_config
    )
    load_job.result()  # Wait for upload to complete

    # Step B: Perform Atomic MERGE into partitioned destination table
    merge_query = f"""
    MERGE INTO `{TARGET_TABLE}` AS target
    USING (
      SELECT 
        TIMESTAMP(raw_timestamp) AS timestamp_utc,
        area_code,
        CAST(actual_load AS NUMERIC) AS actual_load_mw,
        CAST(forecasted_load AS NUMERIC) AS forecasted_load_mw
      FROM `{TEMP_STAGING_TABLE}`
    ) AS source
    ON target.timestamp_utc = source.timestamp_utc 
    AND target.area_code = source.area_code

    WHEN MATCHED THEN
      UPDATE SET 
        actual_load_mw = source.actual_load_mw,
        forecasted_load_mw = source.forecasted_load_mw,
        ingested_at = CURRENT_TIMESTAMP()

    WHEN NOT MATCHED THEN
      INSERT (timestamp_utc, area_code, actual_load_mw, forecasted_load_mw, ingested_at)
      VALUES (source.timestamp_utc, source.area_code, source.actual_load_mw, source.forecasted_load_mw, CURRENT_TIMESTAMP());
    """

    print("Executing BigQuery MERGE transaction...")
    query_job = bq_client.query(merge_query)
    query_job.result()  # Wait for query execution
    
    print("Successfully merged data into production BigQuery raw table!")

# ------------------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    df_load = fetch_entsoe_data()
    if not df_load.empty:
        load_to_bigquery(df_load)
    else:
        print("No data received from ENTSO-E API.")
