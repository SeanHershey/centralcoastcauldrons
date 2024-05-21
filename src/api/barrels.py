from sqlite3 import IntegrityError
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ 
    Deliver barrels takes a list of barrels iterates over them adding to 
    ml and subtracting gold as appropriate.
    """
    print(f"barrels delivered: {barrels_delivered} order id: {order_id}")

    with db.engine.begin() as connection:
        try:
            connection.execute(sqlalchemy.text(
                "INSERT INTO processed (job_id, type, description) VALUES (:order_id, 'barrels', :description)"), 
                [{"order_id":order_id, "description":f"{barrels_delivered}"}])
        except IntegrityError as e:
            return "OK"
        
        gold_paid = 0
        ml = [0,0,0,0]
        
        for barrel in barrels_delivered:
            gold_paid += barrel.price * barrel.quantity

            for i in range(4):
                if (barrel.potion_type[i] > 0):
                    ml[i] += barrel.ml_per_barrel * barrel.quantity

        connection.execute(sqlalchemy.text(
            "INSERT INTO gold_ledger (gold) VALUES (-:gold)"),
            [{"gold":gold_paid}])
        
        connection.execute(sqlalchemy.text(
            "INSERT INTO ml_ledger (red, green, blue, dark) VALUES (:red, :green, :blue, :dark)"),
            [{"red":ml[0], "green":ml[1], "blue":ml[2], "dark":ml[3]}])

    print(f"gold paid: {gold_paid}, ml: {ml})")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Wholesale purchase plan iterates over the ml types and the wholesale catalog
    determining which barrels to buy by the criteria of bigger then more is better.
    """
    print(f"barrel catalog: {wholesale_catalog}")

    with db.engine.begin() as connection:
        ml_inventory = connection.execute(sqlalchemy.text(
            "SELECT SUM(red), SUM(green), SUM(blue), SUM(dark) FROM ml_ledger")).one()
        
        gold = connection.execute(sqlalchemy.text(
            "SELECT SUM(gold) FROM gold_ledger")).scalar_one()
        
        ml_total_capacity = connection.execute(sqlalchemy.text(
            "SELECT SUM(ml) FROM capacity_ledger")).scalar_one()
        
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(quantity) FROM potion_ledger")).scalar_one()
        
        total_capacity = connection.execute(sqlalchemy.text(
            "SELECT SUM(potions) FROM capacity_ledger")).scalar_one()
        
        current_ml = sum(ml_inventory)
        ml_capacity = ml_total_capacity - current_ml

        # STRATEGY
        # - for each ml buy barrels that brings ml closest to the target ml which is 90% capacity
        TARGET_ML = ml_capacity * 0.9
        # - if gold and capacity is a multiple above all large barrels start buying that multiple
        PRICE_LARGE = 2250
        ML_LARGE = 40000
        quantity = min([(gold // (PRICE_LARGE * 2)) + 1, (ml_capacity // (ML_LARGE * 2)) + 1])

        barrel_purchases = []

        for i, ml in enumerate(ml_inventory):
            #late game stop buying
            break

            barrel_purchase = None
            price = None
            ml_add = 0

            for barrel in wholesale_catalog:
                if ((total_potions / total_capacity < 0.8 or current_ml / ml_total_capacity < 0.5) and # not prioritizing gold for capacity
                    barrel.ml_per_barrel * quantity <= ml_capacity and # have the capacity
                    barrel.potion_type[i] > 0 and # right type
                    barrel.quantity >= quantity and # has the desired quantity 
                    barrel.price * quantity <= gold and # affordable
                    barrel.ml_per_barrel * quantity > ml_add and # highest ml content
                    ml + barrel.ml_per_barrel * quantity <= TARGET_ML): # closest to target
            
                    barrel_purchase = {"sku":barrel.sku, "quantity":quantity}
                    price = barrel.price * quantity
                    ml_add = barrel.ml_per_barrel * quantity

            if barrel_purchase is not None:
                barrel_purchases.append(barrel_purchase)
                gold -= price
                ml_capacity -= ml_add

    print(f"barrel plan: {barrel_purchases}")
    return barrel_purchases
