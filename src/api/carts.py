from sqlite3 import IntegrityError
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    if search_page == "":
        search_page = 0

    if sort_col.split(":")[0] == "search_sort_options":
        sort_col = sort_col.split(":")[1]

    if sort_order.split(":")[0] == "search_sort_order":
        sort_order = sort_order.split(":")[1]

    with db.engine.connect() as connection:
        result = connection.execute(sqlalchemy.text(
            f"""
                SELECT timestamp, line_item_total, potion_sku, item_sku, customer_name, id FROM orders
                WHERE 1=1
                {("" if customer_name == "" else "AND customer_name ILIKE '%" + customer_name + "%'")}
                {("" if potion_sku == "" else "AND potion_sku ILIKE '%" + potion_sku + "%'")}
                ORDER BY {sort_col} {sort_order}
                LIMIT 6
                OFFSET :page
            """),
            [{"page":search_page}])

        next = ""
        results = []

        for i, row in enumerate(result):
            if i == 5:
                next = int(search_page) + 5
                break

            results.append(
                {
                    "line_item_id": row.id,
                    "item_sku": row.item_sku,
                    "customer_name": row.customer_name,
                    "line_item_total": row.line_item_total,
                    "timestamp": row.timestamp,
                }
            )
        
    json = [
        {
            "previous": ("" if int(search_page) - 5 < 0 else int(search_page) - 5),
            "next": next,
            "results": results
        }]

    return json


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    for customer in customers:
        with db.engine.begin() as connection:
            try:
                connection.execute(sqlalchemy.text(
                    "INSERT INTO visits (customer_name, character_class, level) VALUES (:customer_name, :character_class, :level)"), 
                    [{"customer_name":customer.customer_name, "character_class":customer.character_class, "level":customer.level}])
            except IntegrityError as e:
                return "OK"

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """
    Create cart insert a row into cart.
    """
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(
            "INSERT INTO cart (customer_name, character_class) VALUES (:customer_name, :character_class) RETURNING id"),
            [{"customer_name":new_cart.customer_name, "character_class":new_cart.character_class}]).scalar_one()

    print(f"new cart id: {cart_id}")
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Set item quantity takes a cart and sku and updates or inserts a quantity as a cart item
    """
    print(f"cart: {cart_id}, set item quantity: {item_sku} to {cart_item.quantity}")

    with db.engine.begin() as connection:
        cart_items = connection.execute(sqlalchemy.text(
            "SELECT sku, quantity FROM cart_items WHERE cart = (:cart_id)"),
            [{"cart_id":cart_id}])

        # update
        updates = 0
        for item in cart_items:
            if item.sku == item_sku:
                updates += 1
                connection.execute(sqlalchemy.text(
                    "UPDATE cart_items SET quantity = (:quantity) WHERE sku = (:item_sku) and cart = (:cart_id)"),
                    [{"quantity":str(cart_item.quantity), "item_sku":item_sku, "cart_id":cart_id}])

        # insert
        if updates == 0:
            connection.execute(sqlalchemy.text(
                "INSERT INTO cart_items (cart, sku, quantity) VALUES (:cart_id, :item_sku, :quantity)"),
                [{"cart_id":cart_id, "item_sku":item_sku, "quantity":str(cart_item.quantity)}])

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    checkout takes the cart and buys the sku and quantity associated
    """

    with db.engine.begin() as connection:
        cart_items = connection.execute(sqlalchemy.text(
            "SELECT sku, quantity FROM cart_items WHERE cart = (:cart_id)"),
            [{"cart_id":cart_id}])
        
        customer = connection.execute(sqlalchemy.text(
            "SELECT customer_name FROM cart WHERE id = (:cart_id)"),
            [{"cart_id":cart_id}]).scalar_one()
        
        catalog = list(connection.execute(sqlalchemy.text(
            "SELECT sku, name, price FROM catalog")))

        payment = 0
        total = 0

        for item in cart_items:
            for sku, name, price in catalog:
                if item.sku == sku:
                    payment += price * item.quantity
                    total += item.quantity
                    connection.execute(sqlalchemy.text(
                        "INSERT INTO potion_ledger (sku, quantity) VALUES (:sku, -:quantity)"),
                        [{"sku":sku, "quantity":item.quantity}])
                    
                    connection.execute(sqlalchemy.text(
                        "INSERT INTO orders (line_item_total, potion_sku, item_sku, customer_name) VALUES (:quantity, :sku, :item_sku, :customer)"),
                        [{"quantity":item.quantity, "sku":sku, "item_sku":f"{item.quantity} {name}", "customer":customer}])
                    
        connection.execute(sqlalchemy.text(
            "INSERT INTO gold_ledger (gold) VALUES (:gold)"),
            [{"gold":payment}])
    
    print(f"checkout: {cart_id}, potions: {total}, paid: {payment}")
    return {"total_potions_bought":total, "total_gold_paid":payment}
