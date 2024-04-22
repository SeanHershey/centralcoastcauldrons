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
            results = connection.execute(sqlalchemy.text("SELECT sku, name, type, quantity, price FROM catalog"))

    catalog = []

    for item in results:
        if item.quantity > 0:
            catalog.append({
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "price": item.price,
                "potion_type": item.type
            })
    
    return catalog
    
