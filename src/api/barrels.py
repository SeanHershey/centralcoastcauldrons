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

    for barrel in barrels_delivered:
        if  (barrel.quantity > 0):
            with db.engine.begin() as connection:
                gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
                num_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
                num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
                num_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar_one()
            
            gold -= barrel.price

            if (barrel.potion_type[0] > 0):
                num_red_ml += barrel.ml_per_barrel * barrel.potion_type[0] * barrel.quantity
            elif (barrel.potion_type[1] > 0):
                num_green_ml += barrel.ml_per_barrel * barrel.potion_type[1] * barrel.quantity
            elif (barrel.potion_type[2] > 0):
                num_blue_ml += barrel.ml_per_barrel * barrel.potion_type[2] * barrel.quantity

            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(num_red_ml)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = " + str(num_green_ml)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = " + str(num_blue_ml)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold)))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        num_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()

    sku = ""
    quantity = 0

    if num_red_potions + num_green_potions + num_blue_potions < 50:
        if (num_red_potions <= num_green_potions) & (num_red_potions <= num_blue_potions):
            for barrel in wholesale_catalog:
                if (barrel.potion_type[0] > 0) & (barrel.price < gold):
                        sku = "SMALL_RED_BARREL"
                        quantity = 1
        elif (num_green_potions <= num_red_potions) & (num_green_potions <= num_blue_potions):
            for barrel in wholesale_catalog:
                if (barrel.potion_type[1] > 0) & (barrel.price < gold):
                        sku = "SMALL_GREEN_BARREL"
                        quantity = 1
        elif (num_blue_potions <= num_red_potions) & (num_blue_potions <= num_green_potions):
            for barrel in wholesale_catalog:
                if (barrel.potion_type[1] > 0) & (barrel.price < gold):
                        sku = "SMALL_BLUE_BARREL"
                        quantity = 1

    if quantity > 0:
        return [
            {
                "sku": sku,
                "quantity": quantity,
            }
        ]
    else:
        return []
