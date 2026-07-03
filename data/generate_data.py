"""
Synthetic data generator for the Brazilian E-Commerce Sales dashboard.

Generates three CSV files that feed the Power BI semantic model:
  - dim_customers.csv  (customer dimension)
  - dim_products.csv   (product dimension)
  - fact_sales.csv     (sales fact table, one row per order line)

Only the Python standard library is used, so it runs anywhere:
  python generate_data.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reproducible output

OUTPUT_DIR = Path(__file__).parent
START_DATE = date(2024, 1, 1)
END_DATE = date(2026, 6, 30)
NUM_CUSTOMERS = 1500
NUM_ORDERS = 18000

# ---------------------------------------------------------------------------
# Geography: Brazilian states grouped into the five official regions.
# Weights roughly follow e-commerce market share by region.
# ---------------------------------------------------------------------------
STATES = [
    # (state, region, sample cities, weight)
    ("SP", "Sudeste", ["São Paulo", "Campinas", "Santos", "Ribeirão Preto"], 30),
    ("RJ", "Sudeste", ["Rio de Janeiro", "Niterói", "Petrópolis"], 12),
    ("MG", "Sudeste", ["Belo Horizonte", "Uberlândia", "Juiz de Fora"], 10),
    ("ES", "Sudeste", ["Vitória", "Vila Velha"], 2),
    ("PR", "Sul", ["Curitiba", "Londrina", "Maringá"], 6),
    ("RS", "Sul", ["Porto Alegre", "Caxias do Sul", "Pelotas"], 6),
    ("SC", "Sul", ["Florianópolis", "Joinville", "Blumenau"], 4),
    ("BA", "Nordeste", ["Salvador", "Feira de Santana"], 5),
    ("PE", "Nordeste", ["Recife", "Olinda", "Caruaru"], 4),
    ("CE", "Nordeste", ["Fortaleza", "Juazeiro do Norte"], 3),
    ("RN", "Nordeste", ["Natal", "Mossoró"], 1),
    ("PB", "Nordeste", ["João Pessoa", "Campina Grande"], 1),
    ("MA", "Nordeste", ["São Luís", "Imperatriz"], 1),
    ("GO", "Centro-Oeste", ["Goiânia", "Anápolis"], 3),
    ("DF", "Centro-Oeste", ["Brasília"], 3),
    ("MT", "Centro-Oeste", ["Cuiabá", "Rondonópolis"], 1),
    ("MS", "Centro-Oeste", ["Campo Grande", "Dourados"], 1),
    ("PA", "Norte", ["Belém", "Ananindeua"], 2),
    ("AM", "Norte", ["Manaus"], 2),
    ("TO", "Norte", ["Palmas"], 1),
]

FIRST_NAMES = [
    "Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Hugo",
    "Isabela", "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia",
    "Pedro", "Rafaela", "Samuel", "Tatiane", "Vinícius", "Beatriz", "Caio",
    "Débora", "Enzo", "Fernanda", "Gustavo", "Helena", "Igor", "Júlia", "Thiago",
]
LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves",
    "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho",
    "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa",
]

# ---------------------------------------------------------------------------
# Product catalog: category -> (subcategory, base product names, price range)
# Prices in BRL. Cost is derived from price with a category-typical margin.
# ---------------------------------------------------------------------------
CATALOG = {
    "Eletrônicos": [
        ("Smartphones", ["Smartphone Galaxy X", "Smartphone Moto Edge", "Smartphone iPro"], (1200, 4500), 0.78),
        ("Notebooks", ["Notebook Ultra 14", "Notebook Gamer Z", "Notebook Slim Air"], (2500, 7500), 0.80),
        ("Áudio", ["Fone Bluetooth Pulse", "Caixa de Som JX", "Headset Gamer HX"], (90, 700), 0.62),
        ("Acessórios", ["Carregador Turbo 30W", "Cabo USB-C 2m", "Power Bank 10000mAh", "Mouse Sem Fio Pro", "Teclado Mecânico K7"], (25, 350), 0.55),
    ],
    "Moda": [
        ("Roupas Masculinas", ["Camiseta Básica Algodão", "Calça Jeans Slim", "Jaqueta Corta-Vento", "Bermuda Sarja"], (40, 280), 0.45),
        ("Roupas Femininas", ["Vestido Midi Floral", "Blusa Cropped", "Calça Legging Fit", "Saia Jeans"], (45, 320), 0.45),
        ("Calçados", ["Tênis Runner Flex", "Sapatênis Casual", "Sandália Comfort", "Bota Coturno"], (80, 480), 0.52),
    ],
    "Casa e Decoração": [
        ("Cozinha", ["Jogo de Panelas Antiaderente", "Air Fryer 4L", "Liquidificador Turbo", "Jogo de Facas Inox"], (60, 900), 0.58),
        ("Decoração", ["Luminária de Mesa LED", "Quadro Decorativo Abstrato", "Tapete Sala 2x1.5m", "Espelho Redondo 60cm"], (35, 450), 0.48),
        ("Cama e Banho", ["Jogo de Cama Queen 4 Peças", "Kit Toalhas Premium", "Edredom Casal"], (70, 400), 0.50),
    ],
    "Esporte e Lazer": [
        ("Fitness", ["Halteres 10kg Par", "Tapete de Yoga", "Corda de Pular Pro", "Kit Elásticos de Treino"], (30, 350), 0.50),
        ("Ciclismo", ["Bicicleta Aro 29", "Capacete MTB", "Farol Recarregável Bike"], (60, 2200), 0.65),
        ("Camping", ["Barraca 4 Pessoas", "Mochila Trilha 50L", "Garrafa Térmica 1L"], (50, 800), 0.55),
    ],
    "Beleza e Saúde": [
        ("Cabelos", ["Kit Shampoo e Condicionador", "Secador Profissional 2000W", "Chapinha Cerâmica"], (35, 420), 0.48),
        ("Skincare", ["Sérum Vitamina C", "Protetor Solar FPS 60", "Creme Hidratante Facial"], (30, 220), 0.42),
        ("Perfumaria", ["Perfume Essence 100ml", "Body Splash Tropical"], (60, 380), 0.40),
    ],
    "Livros e Papelaria": [
        ("Livros", ["Box Trilogia Fantasia", "Romance Best-Seller", "Livro de Negócios", "HQ Edição Especial"], (25, 180), 0.60),
        ("Papelaria", ["Caderno Inteligente A5", "Kit Canetas Coloridas", "Planner Anual", "Mochila Escolar Reforçada"], (15, 250), 0.50),
    ],
}


def build_customers():
    state_pool = []
    for state, region, cities, weight in STATES:
        state_pool.extend([(state, region, cities)] * weight)

    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        state, region, cities = random.choice(state_pool)
        customers.append({
            "customer_id": f"C{i:05d}",
            "customer_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "city": random.choice(cities),
            "state": state,
            "region": region,
        })
    return customers


def build_products():
    products = []
    pid = 1
    for category, subcats in CATALOG.items():
        for subcategory, names, (low, high), margin in subcats:
            for name in names:
                price = round(random.uniform(low, high), 2)
                cost = round(price * (1 - margin) + random.uniform(-0.03, 0.03) * price, 2)
                products.append({
                    "product_id": f"P{pid:04d}",
                    "product_name": name,
                    "category": category,
                    "subcategory": subcategory,
                    "unit_price": price,
                    "unit_cost": max(cost, round(price * 0.15, 2)),
                })
                pid += 1
    return products


def month_weight(d: date) -> float:
    """Seasonality: Black Friday (Nov) and Christmas (Dec) peak, plus
    Dia das Mães (May) and Dia dos Consumidores (Mar) bumps."""
    weights = {1: 0.85, 2: 0.85, 3: 1.0, 4: 0.9, 5: 1.1, 6: 0.95,
               7: 0.9, 8: 0.95, 9: 0.95, 10: 1.05, 11: 1.6, 12: 1.35}
    return weights[d.month]


def growth_weight(d: date) -> float:
    """Business grows ~20% per year across the window."""
    days_in = (d - START_DATE).days
    return 1.0 + 0.20 * (days_in / 365.0)


def build_sales(customers, products):
    # Build a weighted pool of dates so order volume follows seasonality + growth.
    all_days = []
    d = START_DATE
    while d <= END_DATE:
        w = month_weight(d) * growth_weight(d)
        if d.weekday() >= 5:  # weekends slightly quieter
            w *= 0.8
        all_days.append((d, w))
        d += timedelta(days=1)
    dates = [day for day, _ in all_days]
    weights = [w for _, w in all_days]

    # Some products sell far more than others (long-tail popularity).
    product_weights = [random.uniform(0.3, 3.0) for _ in products]

    rows = []
    for order_num in range(1, NUM_ORDERS + 1):
        order_id = f"O{order_num:06d}"
        order_date = random.choices(dates, weights=weights, k=1)[0]
        customer = random.choice(customers)
        num_lines = random.choices([1, 2, 3, 4], weights=[55, 25, 13, 7], k=1)[0]
        chosen = random.choices(products, weights=product_weights, k=num_lines)

        for product in chosen:
            quantity = random.choices([1, 2, 3, 5], weights=[70, 20, 7, 3], k=1)[0]
            # Discounts are deeper and more frequent in November (Black Friday).
            if order_date.month == 11 and random.random() < 0.55:
                discount = round(random.uniform(0.10, 0.40), 2)
            elif random.random() < 0.20:
                discount = round(random.uniform(0.05, 0.20), 2)
            else:
                discount = 0.0
            rows.append({
                "order_id": order_id,
                "order_date": order_date.isoformat(),
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": product["unit_price"],
                "discount_pct": discount,
            })
    rows.sort(key=lambda r: (r["order_date"], r["order_id"]))
    return rows


def write_csv(filename, rows):
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):>6} rows -> {path.name}")


if __name__ == "__main__":
    customers = build_customers()
    products = build_products()
    sales = build_sales(customers, products)

    write_csv("dim_customers.csv", customers)
    write_csv("dim_products.csv", products)
    write_csv("fact_sales.csv", sales)
