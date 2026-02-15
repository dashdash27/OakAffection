## 🛒 E-commerce Platform (Production Ready)

**🔗 Live Demo**: [https://oakaffection.ru](https://oakaffection.ru)  
**Статус проекта**: Запущен в Production.  
**Стек**: Python, Flask, PostgreSQL, SQLAlchemy, Pytest, Docker, Nginx, JS (Vanilla)

<p float="left">
  <img width="48%" alt="hero section" src="https://github.com/user-attachments/assets/8922cfa1-29d8-47b8-b045-e54f5e03bc3e" />
  <img width="48%" alt="details" src="https://github.com/user-attachments/assets/17e16df1-074e-4554-86ee-2e3e30f3874f" />
</p>


### 🎯 Обзор проекта
Полнофункциональная платформа для электронной коммерции, созданная «с нуля»: от проектирования архитектуры и дизайна до настройки серверной инфраструктуры и деплоя.


### 🚀 Особенности
- Защищенная панель администратора собственной разработки (Flask-Login).
- Темная/светлая темы.
- Динамический каталог товаров с генерацией SEO-friendly URL (slug) и возможностью изменять содержимое тегов, влияющих на seo.
- Автоматическая генерация Sitemap и техническая SEO-оптимизация.

### 📈 Roadmap
1. Корзина на стороне клиента (LocalStorage) с серверной валидацией цен и синхронизацией вкладок.
2. Интеграция с внешними API платежных систем и систем логистики для оформления заказов.
3. Внедрение кэширования Redis для ускорения выдачи каталога.

### 🛠 Установка и запуск (Local Dev)
1. Клонировать репозиторий и установить зависимости:
    ```
    git clone https://github.com/dashdash27/OakAffection.git
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt


2. Создайте файл .env и укажите данные для подключения к вашей локальной базе PostgreSQL (SQLALCHEMY_DATABASE_URI, SECRET_KEY).

3. Инициализация БД:

    ```
    flask db upgrade  # Создаст структуру таблиц через миграции Alembic

4. Запуск:
    
    ```
    python run.py
    ```

    Note: Проект поддерживает динамическое управление категориями. Для корректного отображения витрины после первого запуска рекомендуется инициализировать структуру каталога через административную панель.



