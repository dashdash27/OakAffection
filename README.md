# 🛒 E-commerce Platform (Full-Cycle Development)
**High-performance online store with a custom CMS and a frictionless "No-Auth" shopping experience.**

🌐[Live Demo](https://oakaffection.ru)  

---

### 📸 Interface Preview
*Strategic Mobile-First approach with adaptive Light/Dark themes.*

<img width="100%" alt="screenshot" src="https://github.com/user-attachments/assets/afd63aa8-05d2-4bf5-90c3-89af3d6ab456" />

---

### 🛠 Tech Stack
- **Backend:** `Python (Flask)`, `PostgreSQL`, `SQLAlchemy`, `Alembic`, `Pytest`.
- **Infrastructure:** `Nginx`, `Gunicorn`, `Linux (VPS)`, `SSL`.
- **Frontend:** `Vanilla JS (ES6+)`, `HTML5/CSS3`, `Mobile First Design`.

**Deployment Workflow:** Established a protected **Staging environment** on a subdomain to test database migrations and new features before the final release.

---

### 🔥 Key Engineering Challenges

#### 🛒 Smart Cart & Synchronization
Designed to maximize conversion by removing registration barriers.
*   **Frictionless Checkout:** Users can start shopping instantly. No sign-up required to manage the cart.
*   **Real-time Sync:** Used **BroadcastChannel API** to sync cart data across all open browser tabs instantly without extra server calls.
*   **Dynamic Pricing:** Automated discount logic that recalculates the total in real-time within the cart.

#### 📩 One-Click Order Sharing
Implemented a unique manual order placement system to minimize user friction.
*   **Copy Order Summary:** A dedicated feature that formats the entire cart content into a clean text snippet.
*   **Social Integration:** Users can instantly copy their order details and send them via messengers or email for quick processing.


#### 📈 Performance & SEO
*   **Zero Frameworks:** High-speed frontend built with **Vanilla JS**, ensuring lightning-fast load times.
*   **Asset Optimization:** Integrated **Lazy Loading** to reduce page weight.
*   **Semantic Web:** Structured metadata and semantic tags for top-tier visibility in Google/Yandex search results.

---

### 🚀 Roadmap 
Currently integrating external Logistics and Payment Gateway APIs. Migrating to an asynchronous architecture (Asyncio, HTTPX) for parallel API orchestration to improve system throughput.

---


### 📦 Local Development Setup
1. Clone the repository and prepare the environment:
    ```
    git clone https://github.com/dashdash27/OakAffection.git
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt


2. Create a .env file in the root directory and provide your local PostgreSQL connection details and application settings: SQLALCHEMY_DATABASE_URI, SECRET_KEY.

3. Initialize the Database:

    ```
    flask db upgrade 

4. Run the Application:
    
    ```
    python run.py
    ```

    Note: The project features dynamic category management. After the first launch, it is recommended to initialize the catalog structure through the Admin Panel to correctly display the storefront.


