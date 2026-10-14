import sqlite3
import requests
from database import DB_NAME, get_db_connection

def fetch_and_store_rates():
    """Fetches real-time exchange rates and populates the local matrix."""
    # Corrected to the actual open-access API endpoint
    url = "https://open.er-api.com/v6/latest/USD"
    
    print("🔄 Fetching live FX rates...")
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch rates from API. HTTP Status: {response.status_code}")
            return
            
        data = response.json()
        
        if data.get("result") != "success":
            print("❌ API returned a failure status.")
            return
            
        rates = data.get("rates", {})
        
        # We target our core African currencies
        target_currencies = ['NGN', 'GHS', 'KES', 'ZAR', 'EGP', 'USD']
        
        # Filter rates to only what we need
        filtered_rates = {k: v for k, v in rates.items() if k in target_currencies}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("📊 Updating local cross-currency matrix...")
        # Calculate cross rates (e.g., NGN to GHS) and save to database
        for src in target_currencies:
            for tgt in target_currencies:
                if src == tgt:
                    continue
                    
                # Cross-rate calculation formula via USD base
                usd_to_src = filtered_rates.get(src)
                usd_to_tgt = filtered_rates.get(tgt)
                
                if usd_to_src and usd_to_tgt:
                    cross_rate = (1.0 / usd_to_src) * usd_to_tgt
                    
                    # Store or replace rate in the database matrix
                    cursor.execute('''
                        INSERT OR REPLACE INTO fx_rates 
                        (source_currency, target_currency, rate, liquidity_fee_percentage)
                        VALUES (?, ?, ?, ?)
                    ''', (src, tgt, cross_rate, 0.01)) # Default 1% processing corridor fee
                    
        conn.commit()
        conn.close()
        print("✅ FX Rate Matrix successfully synchronized in the database.")
        
    except Exception as e:
        print(f"❌ Error during ingestion: {str(e)}")

if __name__ == "__main__":
    fetch_and_store_rates()
