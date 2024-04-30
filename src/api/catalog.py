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
            "SELECT sku, name, price, type FROM catalog"))

        catalog = []

        for potion in results:
            quantity = connection.execute(sqlalchemy.text(
                "SELECT SUM(quantity) FROM potion_ledger WHERE sku = (:sku)"),
                [{"sku":potion.sku}]).scalar_one()

            if (quantity is not None) and (quantity > 0):
                catalog.append({
                    "sku": potion.sku,
                    "name": potion.name,
                    "quantity": quantity,
                    "price": potion.price,
                    "potion_type": potion.type
                })
    
    print(f"catalog: {catalog}")
    return catalog
    
