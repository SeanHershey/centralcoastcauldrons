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
        if (barrel.potion_type[1] > 0) & (barrel.quantity > 0):
            with db.engine.begin() as connection:
                gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
                num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
            
            gold -= barrel.price
            num_green_ml += barrel.ml_per_barrel * barrel.potion_type[1]

            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = " + str(num_green_ml)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold)))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    sku = ""
    quantity = 0

    with db.engine.begin() as connection:
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()

    if num_green_potions < 10:
        for barrel in wholesale_catalog:
            if (barrel.potion_type[1] > 0) & (barrel.price < gold) & (barrel.quantity > 0):
                    sku = "SMALL_GREEN_BARREL"
                    quantity = 1

    return [
        {
            "sku": sku,
            "quantity": quantity,
        }
    ]
