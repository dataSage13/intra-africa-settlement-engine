from router import process_settlement_request

def run_simulation():
    print("📈 --- STARTING PAPSS LIQUIDITY STRESS TEST ---")
    
    # 1. Test case: An astronomical request to Ghana that should overwhelm its low reserve pool
    print("\n🚨 Test Case 1: Overwhelming a low-liquidity target pool...")
    huge_request = process_settlement_request("NGN", "GHS", 50_000_000)
    print(f"Engine Output: {huge_request}")
    
    # 2. Test case: A small transaction that easily fits within available reserves
    print("\n🟢 Test Case 2: Standard transaction within safe limits...")
    small_request = process_settlement_request("KES", "EGP", 5_000)
    print(f"Engine Output: {small_request}")

if __name__ == "__main__":
    run_simulation()
