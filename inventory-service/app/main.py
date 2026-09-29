import os
import logging
from itertools import count
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator

APP_NAME = os.getenv("APP_NAME", "Inventory Management System")
APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SECRET_KEY = os.getenv("SECRET_KEY", "inventory-super-secret-key")

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("inventory")

app = FastAPI(title=APP_NAME, description="REST API for products, stock and suppliers with monitoring and logging.", version=APP_VERSION)
Instrumentator().instrument(app).expose(app)

products: Dict[int, dict] = {}
suppliers: Dict[int, dict] = {}
stock: Dict[int, dict] = {}
product_ids = count(1)
supplier_ids = count(1)
stock_ids = count(1)

class Product(BaseModel):
    name: str = Field(min_length=2)
    sku: str = Field(min_length=2)
    category: str = Field(min_length=1)
    price: float = Field(gt=0)
    supplier_id: int = Field(gt=0)

class Supplier(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=5)
    phone: str = Field(min_length=5)

class StockUpdate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=0)
    location: str = Field(min_length=1)

@app.get("/", tags=["System"])
def root():
    return {"message": f"{APP_NAME} API is running", "version": APP_VERSION}

@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy"}

@app.get("/products", tags=["Products"])
def get_products() -> List[dict]:
    return list(products.values())

@app.post("/products", status_code=201, tags=["Products"])
def create_product(product: Product):
    if product.supplier_id not in suppliers:
        raise HTTPException(status_code=404, detail="Supplier not found")
    product_id = next(product_ids)
    data = {"id": product_id, **product.model_dump()}
    products[product_id] = data
    logger.info("Product created id=%s sku=%s", product_id, product.sku)
    return data

@app.get("/products/{product_id}", tags=["Products"])
def get_product(product_id: int):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    return products[product_id]

@app.put("/products/{product_id}", tags=["Products"])
def update_product(product_id: int, product: Product):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.supplier_id not in suppliers:
        raise HTTPException(status_code=404, detail="Supplier not found")
    products[product_id] = {"id": product_id, **product.model_dump()}
    logger.info("Product updated id=%s", product_id)
    return products[product_id]

@app.delete("/products/{product_id}", tags=["Products"])
def delete_product(product_id: int):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    del products[product_id]
    logger.info("Product deleted id=%s", product_id)
    return {"message": "Product deleted", "id": product_id}

@app.get("/suppliers", tags=["Suppliers"])
def get_suppliers() -> List[dict]:
    return list(suppliers.values())

@app.post("/suppliers", status_code=201, tags=["Suppliers"])
def create_supplier(supplier: Supplier):
    supplier_id = next(supplier_ids)
    data = {"id": supplier_id, **supplier.model_dump()}
    suppliers[supplier_id] = data
    logger.info("Supplier created id=%s", supplier_id)
    return data

@app.get("/suppliers/{supplier_id}", tags=["Suppliers"])
def get_supplier(supplier_id: int):
    if supplier_id not in suppliers:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return suppliers[supplier_id]

@app.put("/suppliers/{supplier_id}", tags=["Suppliers"])
def update_supplier(supplier_id: int, supplier: Supplier):
    if supplier_id not in suppliers:
        raise HTTPException(status_code=404, detail="Supplier not found")
    suppliers[supplier_id] = {"id": supplier_id, **supplier.model_dump()}
    logger.info("Supplier updated id=%s", supplier_id)
    return suppliers[supplier_id]

@app.delete("/suppliers/{supplier_id}", tags=["Suppliers"])
def delete_supplier(supplier_id: int):
    if supplier_id not in suppliers:
        raise HTTPException(status_code=404, detail="Supplier not found")
    del suppliers[supplier_id]
    logger.info("Supplier deleted id=%s", supplier_id)
    return {"message": "Supplier deleted", "id": supplier_id}

@app.get("/stock", tags=["Stock"])
def get_stock() -> List[dict]:
    return list(stock.values())

@app.post("/stock", status_code=201, tags=["Stock"])
def update_stock(item: StockUpdate):
    if item.product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    stock_id = next(stock_ids)
    data = {"id": stock_id, **item.model_dump()}
    stock[stock_id] = data
    logger.info("Stock updated id=%s product=%s quantity=%s", stock_id, item.product_id, item.quantity)
    return data

@app.get("/stock/{stock_id}", tags=["Stock"])
def get_stock_item(stock_id: int):
    if stock_id not in stock:
        raise HTTPException(status_code=404, detail="Stock record not found")
    return stock[stock_id]

@app.delete("/stock/{stock_id}", tags=["Stock"])
def delete_stock(stock_id: int):
    if stock_id not in stock:
        raise HTTPException(status_code=404, detail="Stock record not found")
    del stock[stock_id]
    logger.info("Stock record deleted id=%s", stock_id)
    return {"message": "Stock record deleted", "id": stock_id}
