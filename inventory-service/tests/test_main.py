import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app, products, suppliers, stock

client = TestClient(app)

def setup_function():
    products.clear(); suppliers.clear(); stock.clear()

def test_health():
    assert client.get("/health").status_code == 200

def test_create_supplier():
    response = client.post("/suppliers", json={"name":"ABC Supplies","email":"abc@example.com","phone":"9999999999"})
    assert response.status_code == 201
    assert response.json()["name"] == "ABC Supplies"

def test_create_product_requires_supplier():
    response = client.post("/products", json={"name":"Laptop","sku":"LAP-001","category":"Electronics","price":50000,"supplier_id":999})
    assert response.status_code == 404

def test_create_product():
    supplier = client.post("/suppliers", json={"name":"ABC Supplies","email":"abc@example.com","phone":"9999999999"}).json()
    response = client.post("/products", json={"name":"Laptop","sku":"LAP-001","category":"Electronics","price":50000,"supplier_id":supplier["id"]})
    assert response.status_code == 201
    assert response.json()["sku"] == "LAP-001"

def test_stock_update():
    supplier = client.post("/suppliers", json={"name":"ABC Supplies","email":"abc@example.com","phone":"9999999999"}).json()
    product = client.post("/products", json={"name":"Laptop","sku":"LAP-001","category":"Electronics","price":50000,"supplier_id":supplier["id"]}).json()
    response = client.post("/stock", json={"product_id":product["id"],"quantity":25,"location":"Warehouse A"})
    assert response.status_code == 201
    assert response.json()["quantity"] == 25

def test_missing_product():
    assert client.get("/products/999").status_code == 404

def test_metrics():
    assert client.get("/metrics").status_code == 200
