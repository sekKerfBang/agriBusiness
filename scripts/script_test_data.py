"""
Script pour générer des données de test réalistes pour AgriBusiness
Usage: python scripts/create_test_data.py
"""

import os
import sys
import random
from datetime import timedelta
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from django.utils import timezone
from apps.utilisateur.models import Utilisateur, ProducerProfile
from apps.products.models import Category, Product
from apps.orders.models import Order, OrderItem

# Données réalistes
PRODUCTEURS = [
    {"name": "Ferme Bio du Soleil", "location": "Provence", "organic": True, "desc": "Spécialiste tomates et herbes aromatiques bio depuis 2010."},
    {"name": "Les Vergers de Marie", "location": "Normandie", "organic": False, "desc": "Pommes, poires et cidre artisanal."},
    {"name": "Coopérative des Montagnes", "location": "Alpes", "organic": True, "desc": "Fromages et viandes de montagne."},
    {"name": "Jardins de Provence", "location": "Provence", "organic": True, "desc": "Légumes méditerranéens et olives."},
    {"name": "La Ferme des Collines", "location": "Bretagne", "organic": False, "desc": "Laitiers et produits laitiers frais."},
    {"name": "Producteurs Unis du Nord", "location": "Hauts-de-France", "organic": True, "desc": "Céréales et légumes racines bio."},
    {"name": "Le Potager Gourmand", "location": "Île-de-France", "organic": True, "desc": "Légumes anciens et herbes rares."},
    {"name": "Ferme des Étoiles", "location": "Occitanie", "organic": True, "desc": "Fruits exotiques et agrumes."},
]

CATEGORIES = ["Légumes", "Fruits", "Équipements", "Semences", "Produits laitiers", "Viandes", "Céréales", "Herbes aromatiques"]

PRODUITS_PAR_CATEGORIE = {
    "Légumes": ["Tomates cerises", "Courgettes", "Salade romaine", "Carottes", "Pommes de terre", "Poivrons", "Aubergines", "Haricots verts"],
    "Fruits": ["Pommes Golden", "Fraises", "Cerises", "Raisins", "Pêches", "Abricots", "Figues", "Kiwi"],
    "Équipements": ["Serre 6m", "Motoculteur", "Arrosoir auto", "Bêche pro", "Pulvérisateur"],
    "Semences": ["Graines tomates", "Basilic", "Courgettes", "Salade", "Fleurs comestibles"],
    "Produits laitiers": ["Fromage chèvre", "Yaourt nature", "Beurre fermier", "Crème fraîche"],
    "Viandes": ["Poulet fermier", "Boeuf race", "Agneau", "Porc bio"],
    "Céréales": ["Blé ancien", "Avoine", "Riz complet", "Orge"],
    "Herbes aromatiques": ["Basilic", "Menthe", "Persil", "Ciboulette", "Thym", "Romarin"]
}

def create_categories():
    for name in CATEGORIES:
        Category.objects.get_or_create(name=name)
    print("✅ Catégories créées")

def create_producers():
    producers = []
    for data in PRODUCTEURS:
        username = data["name"].lower().replace(" ", "_").replace("é", "e")[:30]
        email = f"{username}@test.com"
        
        user, _ = Utilisateur.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'role': 'ENTREPRISE',
                'phone': f"06{random.randint(0, 99999999):08d}",
                'location': data["location"],
                'is_active': True
            }
        )
        if not user.password:
            user.set_password("demo1234")
            user.save()
        
        profile, created = ProducerProfile.objects.get_or_create(
            user=user,
            defaults={
                'is_organic': data["organic"],
                'description': data["desc"],
                'certifications': "AB, HVE" if data["organic"] else ""
            }
        )
        if created:
            print(f"✅ Producteur créé : {data['name']} ({username})")
        producers.append(profile)
    return producers

def create_products(producers):
    categories = Category.objects.all()
    for producer in producers:
        for _ in range(random.randint(5, 10)):
            cat = random.choice(categories)
            name = random.choice(PRODUITS_PAR_CATEGORIE.get(cat.name, ["Produit divers"]))
            price = round(random.uniform(2.5, 50), 2)
            stock = random.randint(0, 200)
            
            Product.objects.get_or_create(
                producer=producer,
                name=name,
                category=cat,
                defaults={
                    'description': f"{name} de qualité premium par {producer.user.username}.",
                    'price': price,
                    'stock': stock,
                    'is_active': True,
                }
            )
    print(f"✅ {Product.objects.count()} produits créés")

def create_clients(num=12):
    for i in range(1, num + 1):
        username = f"client{i}"
        user, _ = Utilisateur.objects.get_or_create(
            username=username,
            defaults={
                'email': f"client{i}@test.com",
                'role': 'CLIENT',
                'phone': f"07{random.randint(0, 99999999):08d}",
                'location': random.choice(["Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux"]),
                'is_active': True
            }
        )
        if not user.password:
            user.set_password("demo1234")
            user.save()
        print(f"✅ Client créé : {username}")

def create_orders():
    clients = Utilisateur.objects.filter(role='CLIENT')
    products = Product.objects.filter(is_active=True)
    if not clients.exists() or not products.exists():
        print("⚠️ Pas assez de clients ou produits pour créer des commandes")
        return

    for _ in range(25):
        client = random.choice(clients)
        order = Order.objects.create(
            client=client,
            status=random.choice(['PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED']),
            total_amount=0,
            shipping_address=f"{random.randint(1, 200)} rue exemple, {client.location}",
            notes=random.choice(["", "Livraison matin", "Laisser au voisin", "Emballage cadeau"])
        )
        num_items = random.randint(1, 5)
        selected_products = random.sample(list(products), min(num_items, products.count()))
        total = 0
        for prod in selected_products:
            stock = int(prod.stock)
            qty = random.randint(1, min(10, stock if stock > 0 else 1))
            # qty = random.randint(1, min(10, prod.stock if prod.stock > 0 else 1))
            subtotal = qty * prod.price
            OrderItem.objects.create(order=order, product=prod, quantity=qty, unit_price=prod.price, subtotal=subtotal)
            total += subtotal
        order.total_amount = total
        order.total_amount = sum(item.subtotal for item in order.items.all())
        order.save()
    print(f"✅ {Order.objects.count()} commandes créées")

if __name__ == "__main__":
    print("🌾 Génération de données de test pour AgriBusiness...")
    create_categories()
    create_producers()
    create_products(ProducerProfile.objects.all())
    create_clients()
    create_orders()
    print("\n🎉 Données de test générées avec succès !")
    print("   Utilise 'demo1234' comme mot de passe pour tous les comptes de test.")