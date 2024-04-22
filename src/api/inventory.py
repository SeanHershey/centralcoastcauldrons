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
    """ """

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text("SELECT quantity FROM catalog"))

        total_potions = 0
        for item in results:
            total_potions += item.quantity

        red_ml = connection.execute(sqlalchemy.text("SELECT red_ml FROM global_inventory")).scalar_one()
        green_ml = connection.execute(sqlalchemy.text("SELECT green_ml FROM global_inventory")).scalar_one()
        blue_ml = connection.execute(sqlalchemy.text("SELECT blue_ml FROM global_inventory")).scalar_one()

        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
    
    return {"number_of_potions": total_potions, "ml_in_barrels": red_ml + green_ml + blue_ml, "gold": gold}


# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text("SELECT quantity FROM catalog"))

        total_potions = 0
        for item in results:
            total_potions += item.quantity
        
        red_ml = connection.execute(sqlalchemy.text("SELECT red_ml FROM global_inventory")).scalar_one()
        green_ml = connection.execute(sqlalchemy.text("SELECT green_ml FROM global_inventory")).scalar_one()
        blue_ml = connection.execute(sqlalchemy.text("SELECT blue_ml FROM global_inventory")).scalar_one()

    return {
        "potion_capacity": 50 - total_potions,
        "ml_capacity": 10000 - red_ml + green_ml + blue_ml
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

    return "OK"
