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
    """ """
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        try:
            connection.execute(sqlalchemy.text(
                "INSERT INTO processed (job_id, type) VALUES (:order_id, 'barrels')"), 
                [{"order_id":order_id}])
        except IntegrityError as e:
            return "OK"
        
        gold_paid = 0
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0

        for barrel in barrels_delivered:
            gold_paid += barrel.price * barrel.quantity

            if (barrel.potion_type[0] > 0):
                red_ml += barrel.ml_per_barrel * barrel.quantity
            elif (barrel.potion_type[1] > 0):
                green_ml += barrel.ml_per_barrel * barrel.quantity
            elif (barrel.potion_type[2] > 0):
                blue_ml += barrel.ml_per_barrel * barrel.quantity
            elif (barrel.potion_type[3] > 0):
                dark_ml += barrel.ml_per_barrel * barrel.quantity
            else:
                raise Exception("Invalid potion type")

        connection.execute(sqlalchemy.text(
            """
            UPDATE global_inventory SET
            gold = gold - :gold_paid,
            red_ml = red_ml + :red_ml,
            green_ml = green_ml + :green_ml,
            blue_ml = blue_ml + :blue_ml,
            dark_ml = dark_ml + :dark_ml"""),
            [{"gold_paid":gold_paid, "red_ml":red_ml, "green_ml":green_ml, "blue_ml":blue_ml, "dark_ml":dark_ml}])

    print(f"gold_paid: {gold_paid} red_ml: {red_ml} green_ml: {green_ml} blue_ml: {blue_ml} dark_ml: {dark_ml}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(f"barrel_catalog {wholesale_catalog}")

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(
            "SELECT gold, red_ml, green_ml, blue_ml FROM global_inventory")).one()
        
        gold = results.gold
        ml_inventory = [results.red_ml, results.green_ml, results.blue_ml]
        current_ml = sum(ml_inventory)

        # STRATEGY - for each ml buy barrels that brings ml closest to the target ml
        TARGET_ML = 1000

        barrel_purchases = []

        for i, ml in enumerate(ml_inventory):
            barrel_purchase = None
            price = None
            ml_add = 0

            for barrel in wholesale_catalog:
                if len(barrel.potion_type) < 3:
                    break

                if (barrel.potion_type[i] > 0) & (barrel.price <= gold) & (barrel.ml_per_barrel > ml_add) & (ml + barrel.ml_per_barrel <= TARGET_ML):
                    barrel_purchase = {"sku":barrel.sku, "quantity":1}
                    price = barrel.price
                    ml_add = barrel.ml_per_barrel

            if barrel_purchase is not None:
                barrel_purchases.append(barrel_purchase)
                gold -= price
                current_ml += ml_add

    print(f"barrel_purchases: {barrel_purchases}")

    return barrel_purchases
