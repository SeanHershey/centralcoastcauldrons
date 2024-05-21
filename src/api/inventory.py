from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """
    Get inventory returns the total number of potions, ml, and gold.
    """

    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(quantity) FROM potion_ledger")).scalar_one()
        
        total_ml = connection.execute(sqlalchemy.text(
            "SELECT SUM(red + green + blue + dark) FROM ml_ledger")).scalar_one()
        
        gold = connection.execute(sqlalchemy.text(
            "SELECT SUM(gold) FROM gold_ledger")).scalar_one()
    
    print(f"potions: {total_potions}, ml: {total_ml}, gold: {gold}")
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": gold}


# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text(
            "SELECT SUM(gold) FROM gold_ledger")).scalar_one()
        
        total_capacity = connection.execute(sqlalchemy.text(
            "SELECT SUM(potions) FROM capacity_ledger")).scalar_one()
        
        # buy just potion capacity first then buy together
        units = gold // 1000 if total_capacity == 50 else gold // 3000
        
        # late game addition
        units = units // 2

    print(f"capacity plan potion units: {units}, ml units: {0}")
    return {
        "potion_capacity": 0, #units,
        "ml_capacity": 0 #if total_capacity == 50 else units
    }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
                "INSERT INTO capacity_ledger (potions, ml) VALUES (:potions, :ml)"),
                [{"potions":capacity_purchase.potion_capacity * 50, "ml":capacity_purchase.ml_capacity * 10000}])
        
        gold_paid = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000

        connection.execute(sqlalchemy.text(
                "INSERT INTO gold_ledger (gold) VALUES (-:gold)"),
                [{"gold":gold_paid}])
    
    print(f"capacity deliver gold paid: {gold_paid}")
    return "OK"
