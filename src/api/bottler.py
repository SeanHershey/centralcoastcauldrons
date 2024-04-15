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
        num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        num_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()

    for potion in potions_delivered:
        if potion.potion_type[0] > 0:
            num_red_potions += potion.quantity
        elif potion.potion_type[1] > 0:
            num_green_potions += potion.quantity
        elif potion.potion_type[2] > 0:
            num_blue_potions += potion.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = " + str(num_red_potions)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = " + str(num_green_potions)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = " + str(num_blue_potions)))

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
        num_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
        num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar_one()

    order = []

    quantity = num_red_ml // 100
    num_red_ml -= quantity * 100
    print(quantity)
    if quantity > 0:
        order.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quantity,
            }
        )

    quantity = num_green_ml // 100
    num_green_ml -= quantity * 100
    print(quantity)
    if quantity > 0:
        order.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quantity,
            }
        )
    
    quantity = num_blue_ml // 100
    num_blue_ml -= quantity * 100
    print(quantity)
    if quantity > 0:
        order.append(
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": quantity,
            }
        )

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(num_red_ml) + 
                                           ", num_green_ml = " + str(num_green_ml) + 
                                           ", num_blue_ml = " + str(num_blue_ml)))

    print(order)

    return order

if __name__ == "__main__":
    print(get_bottle_plan())