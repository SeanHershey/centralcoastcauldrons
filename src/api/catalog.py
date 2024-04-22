from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    with db.engine.begin() as connection:
        red_potions = connection.execute(sqlalchemy.text("SELECT red_potions FROM global_inventory")).scalar_one()
        green_potions = connection.execute(sqlalchemy.text("SELECT green_potions FROM global_inventory")).scalar_one()
        blue_potions = connection.execute(sqlalchemy.text("SELECT blue_potions FROM global_inventory")).scalar_one()

    catalog = []

    if red_potions > 0:
        catalog.append({
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": red_potions,
            "price": 50,
            "potion_type": [100, 0, 0, 0],
        })
    
    if green_potions > 0:
        catalog.append({
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": green_potions,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        })
    
    if blue_potions > 0:
        catalog.append({
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": blue_potions,
            "price": 50,
            "potion_type": [0, 0, 100, 0],
        })
    
    return catalog
    
