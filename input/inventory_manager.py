"""Inventory Manager - Defect: Mutable global state mutation & invariant breach (negative inventory)."""

import time
from typing import Dict

# Global mutable inventory state
GLOBAL_INVENTORY: Dict[str, int] = {
    "item_a": 10,
    "item_b": 5,
    "item_c": 0
}


def deduct_stock(item_id: str, quantity: int) -> bool:
    """Deducts requested quantity from inventory."""
    global GLOBAL_INVENTORY
    
    # DEFECT 1 (Invariant Breach): Checks stock but does not lock or prevent negative deduction
    # If quantity > current stock, stock becomes negative!
    if item_id in GLOBAL_INVENTORY:
        # Bug: Missing check if GLOBAL_INVENTORY[item_id] >= quantity
        GLOBAL_INVENTORY[item_id] -= quantity  # Can result in negative stock values like -5
        return True
    return False


def concurrent_purchase_simulation(item_id: str, quantity: int):
    """Simulates multi-threaded purchase without mutex locking."""
    # DEFECT 2 (Race Condition / State Mutation): Reads, sleeps (simulating async I/O), then mutates state
    current_stock = GLOBAL_INVENTORY.get(item_id, 0)
    time.sleep(0.01)  # Context switch simulation
    
    # Overwrites state based on stale read value
    GLOBAL_INVENTORY[item_id] = current_stock - quantity
