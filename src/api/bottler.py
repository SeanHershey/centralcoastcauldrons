from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        catalog = connection.execute(sqlalchemy.text(
            "SELECT quantity, sku, type FROM catalog"))

        red_ml, green_ml, blue_ml = connection.execute(sqlalchemy.text(
            "SELECT red_ml, green_ml, blue_ml FROM global_inventory")).one()

        for potion in catalog:
            for delivery in potions_delivered:
                if delivery.potion_type == potion.type:
                    red_ml -= potion.type[0] * delivery.quantity
                    green_ml -= potion.type[1] * delivery.quantity
                    blue_ml -= potion.type[2] * delivery.quantity

                    connection.execute(sqlalchemy.text(
                        "UPDATE global_inventory SET red_ml = :red_ml, green_ml = :green_ml, blue_ml = :blue_ml"),
                        [{"red_ml":red_ml, "green_ml":green_ml, "blue_ml":blue_ml}])

                    connection.execute(sqlalchemy.text(
                        "UPDATE catalog SET quantity = :quantity WHERE sku = :sku"),
                        [{"quantity":str(potion.quantity + delivery.quantity), "sku":potion.sku}])
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        red_ml, green_ml, blue_ml = connection.execute(sqlalchemy.text(
            "SELECT red_ml, green_ml, blue_ml FROM global_inventory")).one()

        order = []

        # MAGIC BOTTLES
        quantity = min([(red_ml // 30), (green_ml // 30), (blue_ml // 30)])
        red_ml -= quantity * 30
        green_ml -= quantity * 30
        blue_ml -= quantity * 30
        if quantity > 0:
            order.append(
                {
                    "potion_type": [30, 30, 30, 0],
                    "quantity": quantity,
                }
            )
        
        # HEALTH BOTTLES
        quantity = red_ml // 100
        red_ml -= quantity * 100
        if quantity > 0:
            order.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": quantity,
                }
            )

        # STAMINA BOTTLES
        quantity = green_ml // 100
        green_ml -= quantity * 100
        if quantity > 0:
            order.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": quantity,
                }
            )
        
        
    print("get_bottle_plan:", order)

    return order

if __name__ == "__main__":
    print(get_bottle_plan())