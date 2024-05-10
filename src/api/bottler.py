from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from sqlite3 import IntegrityError
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
    """
    Deliver bottles takes potions iterates over them and the catalog to subtract from ml
    and add potions.
    """
    print(f"potions delivered: {potions_delivered}, order id: {order_id}")

    with db.engine.begin() as connection:
        try:
            connection.execute(sqlalchemy.text(
                "INSERT INTO processed (job_id, type, description) VALUES (:order_id, 'potions', :description)"), 
                [{"order_id":order_id, "description":f"{potions_delivered}"}])
        except IntegrityError as e:
            return "OK"
        
        catalog = connection.execute(sqlalchemy.text(
            "SELECT sku, type FROM catalog"))

        for potion in catalog:
            for delivery in potions_delivered:
                if delivery.potion_type == potion.type:
                    ml = []
                    
                    for i in range(4):
                        ml.append(potion.type[i] * delivery.quantity)

                    # TODO: build these values then insert only once not in for loop
                    connection.execute(sqlalchemy.text(
                        "INSERT INTO ml_ledger (red, green, blue, dark) VALUES (-:red, -:green, -:blue, -:dark)"),
                        [{"red":ml[0], "green":ml[1], "blue":ml[2], "dark":ml[3]}])
                    
                    connection.execute(sqlalchemy.text(
                        "INSERT INTO potion_ledger (sku, quantity) VALUES (:sku, :quantity)"),
                        [{"sku":potion.sku, "quantity":delivery.quantity}])
    
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        catalog = connection.execute(sqlalchemy.text(
            "SELECT sku, type FROM catalog ORDER BY priority"))
        
        ml_inventory = connection.execute(sqlalchemy.text(
            "SELECT SUM(red), SUM(green), SUM(blue), SUM(dark) FROM ml_ledger")).one()
        
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(quantity) FROM potion_ledger")).scalar_one()
        
        total_capacity = connection.execute(sqlalchemy.text(
            "SELECT SUM(potions) FROM capacity_ledger")).scalar_one()
        
        potion_capacity = total_capacity - total_potions

        ml_list = []
        for i, ml in enumerate(ml_inventory):
            ml_list.append(ml)

        # build order by potion priority
        order = []
        for potion in catalog:
            # find the quantity that can be made
            required = []
            for i in range(4):
                if potion.type[i] > 0:
                    required.append(ml_list[i] // potion.type[i])
            quantity = min(required)

            # capacity limit
            if quantity > potion_capacity:
                quantity = potion_capacity

            # subtract ml available for other potions
            for i in range(4):
                ml_list[i] -= quantity * potion.type[i]

            total_potions += quantity
            potion_capacity -= quantity

            if quantity > 0:
                order.append(
                    {
                        "potion_type": potion.type,
                        "quantity": quantity,
                    }
                )
        
    print(f"bottle plan: {order}")
    return order

if __name__ == "__main__":
    print(get_bottle_plan())