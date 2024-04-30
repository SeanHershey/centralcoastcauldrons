from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    print("reset: gold set to 100, ml/potion quantities set to 0, and capacity set to 50 potions 10000 ml")

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "TRUNCATE TABLE gold_ledger"))
        connection.execute(sqlalchemy.text(
            "INSERT INTO gold_ledger (gold) VALUES (:gold)"),
            [{"gold":100}])
        
        connection.execute(sqlalchemy.text(
            "TRUNCATE TABLE ml_ledger"))
        connection.execute(sqlalchemy.text(
            "INSERT INTO ml_ledger (red, green, blue, dark) VALUES (0, 0, 0, 0)"))
        
        connection.execute(sqlalchemy.text(
            "TRUNCATE TABLE potion_ledger"))
        connection.execute(sqlalchemy.text(
            "INSERT INTO potion_ledger (sku, quantity) VALUES ('NULL_SKU', 0)"))
        
        connection.execute(sqlalchemy.text(
            "TRUNCATE TABLE capacity_ledger"))
        connection.execute(sqlalchemy.text(
            "INSERT INTO capacity_ledger (potions, ml) VALUES (50, 10000)"))

    return "OK"
