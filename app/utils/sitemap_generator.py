from app.models import Product, Category
from app.extensions import BASE_DIR
from app.logger import logger
from app.routes import categories_dict

import xml.etree.ElementTree as ET
from datetime import datetime
import os


def generate_sitemap():
    base_url = "https://oakaffection.ru"
    filepath = os.path.join(BASE_DIR.parent, 'sitemap.xml')

    urlset = ET.Element('urlset', xmlns="https://www.sitemaps.org/schemas/sitemap/0.9")

    def add_url(loc, lastmod):
        url = ET.SubElement(urlset, 'url')
        ET.SubElement(url, 'loc').text = loc
        if lastmod:
            ET.SubElement(url, 'lastmod').text = lastmod.strftime('%Y-%m-%d')
    
    # добавляем главную страницу
    add_url(f"https://oakaffection.ru/", datetime(2025, 12, 7))

    # перебираем все продукты
    products = Product.query.all()
    for product in products:
        product_url = f"https://oakaffection.ru/product/{product.slug}"
        add_url(product_url, product.last_updated)

    categories = Category.query.all()
    for category in categories:
        for key, val in categories_dict.items():
            if val == category.name:
                category_url = f"https://oakaffection.ru/{key}"
                add_url(category_url, category.last_updated)


    ET.indent(urlset, space="  ", level=0)
    tree = ET.ElementTree(urlset)
    tree.write(filepath, encoding='utf-8', xml_declaration=True)

    logger.info("Файл 'sitemap.xml' сгенерирован")