from app.logger import logger 
from app.models import Product, ProductDraft
from app.extensions import db
from app.admin.publish.helpers import create_product_by_draft, delete_draft, delete_product, fill_product_by_draft
from app.utils import generate_sitemap

def publish_all_changes():
    logger.info(">>> Публикация изменений товаров на сайт началась")
    products = Product.query.all()

    orphan_drafts = ProductDraft.query.filter(ProductDraft.product_id.is_(None)).all()
    products_to_delete = Product.query.filter(Product.delete_mark == True).all()
    
    product_drafts = []
    for product in products:
        if product.draft and not product.delete_mark:
            product_drafts.append(product.draft)

    if orphan_drafts != []:
        logger.info("Список новых товаров:")
        for draft in orphan_drafts:
            logger.info(f"-- '{draft.name}'")
    else:
        logger.info("Новых товаров нет")
    
    if product_drafts != []:
        logger.info("Список обновленных товаров:")
        for draft in product_drafts:
            logger.info(f"-- '{draft.name}'")
    else:
        logger.info("Обновленных товаров нет")

    if products_to_delete != []:
        logger.info("Список удаляемых товаров:")
        for product in products_to_delete:
            logger.info(f"-- '{product.name}'")
    else:
        logger.info("Удаляемых товаров нет")
    
    # Создаем новые продукты
    new_products = []
    if orphan_drafts != []:
        logger.info(f">>> Создаются новые товары")
        for draft in orphan_drafts:
            new_product = create_product_by_draft(draft)
            new_products.append(new_product)
            draft.product = new_product
    db.session.add_all(new_products)

    # удаляем черновики-сироты
    if orphan_drafts != []:
        logger.info(">>> Удаляются черновики новых продуктов")
        for draft in orphan_drafts:
            delete_draft(draft)

    # удаляем продукты, отмеченные на удаление
    if products_to_delete != []:
        logger.info(">>> Удаляются продукты, помеченные на удаление")
    for product in products_to_delete:
        delete_product(product)

    for draft in product_drafts:
        logger.info(f"Товар '{draft.name}' обновляется")
        fill_product_by_draft(draft.product, draft)
        delete_draft(draft)
    try:
        db.session.commit()
        logger.info("Изменения успешно подтверждены")
        logger.info("<<< Публикация изменений на сайт закончилась")
        generate_sitemap()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при подтверждении изменений: {str(e)}")
        logger.info("<<< Публикация изменений на сайт закончилась")
        return False
