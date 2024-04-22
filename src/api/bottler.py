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
        red_potions = connection.execute(sqlalchemy.text("SELECT red_potions FROM global_inventory")).scalar_one()
        green_potions = connection.execute(sqlalchemy.text("SELECT green_potions FROM global_inventory")).scalar_one()
        blue_potions = connection.execute(sqlalchemy.text("SELECT blue_potions FROM global_inventory")).scalar_one()

    for potion in potions_delivered:
        if potion.potion_type[0] > 0:
            red_potions += potion.quantity
        elif potion.potion_type[1] > 0:
            green_potions += potion.quantity
        elif potion.potion_type[2] > 0:
            blue_potions += potion.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET red_potions = " + str(red_potions)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET green_potions = " + str(green_potions)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET blue_potions = " + str(blue_potions)))

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT red_ml FROM global_inventory")).scalar_one()
        green_ml = connection.execute(sqlalchemy.text("SELECT green_ml FROM global_inventory")).scalar_one()
        blue_ml = connection.execute(sqlalchemy.text("SELECT blue_ml FROM global_inventory")).scalar_one()

    order = []

    quantity = red_ml // 100
    red_ml -= quantity * 100
    print(quantity)
    if quantity > 0:
        order.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quantity,
            }
        )

    quantity = green_ml // 100
    green_ml -= quantity * 100
    print(quantity)
    if quantity > 0:
        order.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quantity,
            }
        )
    
    quantity = blue_ml // 100
    blue_ml -= quantity * 100
    print(quantity)
    if quantity > 0:
        order.append(
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": quantity,
            }
        )

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET red_ml = " + str(red_ml) + 
                                           ", green_ml = " + str(green_ml) + 
                                           ", blue_ml = " + str(blue_ml)))

    print(order)

    return order

if __name__ == "__main__":
    print(get_bottle_plan())