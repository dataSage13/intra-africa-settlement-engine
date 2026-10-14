import sqlite3
import networkx as nx
import uuid
from database import get_db_connection

def load_fx_graph():
    """Loads currency corridors from the database into a NetworkX directed graph."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all corridors and their exchange rates
    cursor.execute("SELECT source_currency, target_currency, rate, liquidity_fee_percentage FROM fx_rates")
    rows = cursor.fetchall()
    conn.close()
    
    G = nx.DiGraph()
    for row in rows:
        # Cost metric to minimize = exchange rate * (1 + fee percentage)
        # Higher rates/fees cost more, so we want the path minimizing total weight
        cost_weight = row['rate'] * (1.0 + row['liquidity_fee_percentage'])
        G.add_edge(row['source_currency'], row['target_currency'], weight=cost_weight, rate=row['rate'])
        
    return G

def get_liquidity_reserves():
    """Fetches the active central bank liquidity pool balances."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT currency_code, available_liquidity FROM central_bank_reserves")
    rows = cursor.fetchall()
    conn.close()
    return {row['currency_code']: row['available_liquidity'] for row in rows}

def process_settlement_request(source, target, amount):
    """Processes a trade request, handles graph optimization, and logs the execution."""
    tx_id = str(uuid.uuid4())
    G = load_fx_graph()
    reserves = get_liquidity_reserves()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"\n⚡ Processing Trade Request [{tx_id}]: {amount:,.2f} {source} ➡️ {target}")
    
    try:
        # Find the path with the lowest cumulative weight/cost
        path = nx.dijkstra_path(G, source, target, weight='weight')
        
        # Step-by-step verification of liquidity along the chosen network path
        current_amount = amount
        for i in range(len(path) - 1):
            src_node = path[i]
            tgt_node = path[i+1]
            
            # Get exchange rate for this hop
            rate = G[src_node][tgt_node]['rate']
            # Convert the clearing amount into the target node's currency unit
            current_amount = current_amount * rate
            
            # Check if target node has enough reserves to handle the conversion payout
            if reserves.get(tgt_node, 0) < current_amount:
                reason = f"Liquidity shortfall at node '{tgt_node}' (Needed: {current_amount:,.2f}, Available: {reserves.get(tgt_node,0):,.2f})"
                
                cursor.execute('''
                    INSERT INTO settlement_transactions (transaction_id, source_currency, target_currency, amount, status, failure_reason)
                    VALUES (?, ?, ?, ?, 'FAILED_LIQUIDITY', ?)
                ''', (tx_id, source, target, amount, reason))
                conn.commit()
                conn.close()
                
                return {"status": "FAILED_LIQUIDITY", "reason": reason, "path_attempted": " -> ".join(path)}
        
        # If all nodes clear liquidity checks, update reserves for the final node (payout pool)
        new_reserve_balance = reserves[target] - current_amount
        cursor.execute('''
            UPDATE central_bank_reserves 
            SET available_liquidity = ?, last_updated = CURRENT_TIMESTAMP 
            WHERE currency_code = ?
        ''', (new_reserve_balance, target))
        
        # Log successful settlement
        path_str = " -> ".join(path)
        cursor.execute('''
            INSERT INTO settlement_transactions (transaction_id, source_currency, target_currency, amount, settled_amount, routing_path, status)
            VALUES (?, ?, ?, ?, ?, ?, 'SETTLED')
        ''', (tx_id, source, target, amount, current_amount, path_str))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "SETTLED",
            "transaction_id": tx_id,
            "routing_path": path_str,
            "final_payout_amount": round(current_amount, 4)
        }
        
    except nx.NetworkXNoPath:
        reason = "No trading corridor connects these two currencies."
        cursor.execute('''
            INSERT INTO settlement_transactions (transaction_id, source_currency, target_currency, amount, status, failure_reason)
            VALUES (?, ?, ?, ?, 'FAILED_NO_ROUTE', ?)
        ''', (tx_id, source, target, amount, reason))
        conn.commit()
        conn.close()
        return {"status": "FAILED_NO_ROUTE", "reason": reason}

if __name__ == "__main__":
    # Test an initial small transaction that should clear perfectly
    result = process_settlement_request("NGN", "ZAR", 50000)
    print(f"Result: {result}")
