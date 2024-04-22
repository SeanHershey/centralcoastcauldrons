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
        catalog = connection.execute(sqlalchemy.text("SELECT quantity, sku, type FROM catalog"))

        for potion in catalog:
            for delivery in potions_delivered:
                if delivery.potion_type == potion.type:
                    connection.execute(sqlalchemy.text("UPDATE catalog SET quantity = " + str(potion.quantity + delivery.quantity) +
                                                        " WHERE sku = '" + str(potion.sku) + "'"))

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT red_ml FROM global_inventory")).scalar_one()
        green_ml = connection.execute(sqlalchemy.text("SELECT green_ml FROM global_inventory")).scalar_one()
        blue_ml = connection.execute(sqlalchemy.text("SELECT blue_ml FROM global_inventory")).scalar_one()

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
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET red_ml = " + str(red_ml) + 
                                           ", green_ml = " + str(green_ml) + 
                                           ", blue_ml = " + str(blue_ml)))

    print("get_bottle_plan:", order)

    return order

if __name__ == "__main__":
    print(get_bottle_plan())