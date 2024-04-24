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
        results = connection.execute(sqlalchemy.text(
            "SELECT sku, name, quantity, price, type FROM catalog"))

    catalog = []

    for potion in results:
        if potion.quantity > 0:
            catalog.append({
                "sku": potion.sku,
                "name": potion.name,
                "quantity": potion.quantity,
                "price": potion.price,
                "potion_type": potion.type
            })
    
    return catalog
    
