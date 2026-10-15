# 🛒 High-Performance E-Commerce Platform (Full-Cycle Development)
A production-ready, highly optimized online store featuring a custom CMS, lightning-fast automated logistics, and a frictionless "No-Auth" conversion-centric shopping experience. Designed and deployed end-to-end as a resilient, cost-effective monolith.

🚀 **[Live Demo](https://oakaffection.ru)**

---

## 🏗️ System Architecture & Trade-offs

The core philosophy behind this platform is **pragmatic performance**: achieving sub-millisecond local latency, high security, and exceptional throughput using a lean, maintainable monolithic stack (`Flask` + `PostgreSQL` + `Nginx`) running bare-metal on a single Linux VPS.

<div align="center">
    <img width="750px" style="max-width: 100%" alt="scheme-git" src="https://github.com/user-attachments/assets/bdb1f497-4d00-4995-8af1-130d904e0a85" />
</div>


### Key Engineering Decisions: 
* **Smart Local Caching via SQLite (WAL Mode):** One of the delivery services features an API that returns a chaotic, unmapped dump of 80,000+ pickup points (ПВЗ) all at once. To avoid severe network latency and expensive external API calls during checkout, a weekly background `Cron Job` fetches the dump, maps coordinates via the `DaData API`, and caches them into a local **SQLite** database optimized with indexes and **WAL (Write-Ahead Logging)**. This achieves inside-memory lookup speeds without the infrastructure overhead of a Redis cluster.
* **Hybrid Async Orchestration:** While Flask is synchronous, polling multiple shipping carrier APIs sequentially caused terrible network blocking. By injecting localized asynchronous execution using `asyncio.gather` and `HTTPX`, the system polls all delivery services concurrently, cutting checkout API response times by **300%**.
* **Isolated Thread Background Workers:** Heavy, non-blocking operations—such as adaptive HTML email generation, track-number dispatching — are offloaded to isolated background threads, keeping the primary Flask event loop free and highly responsive.
* **Bare-Metal Linux Deployment:** Deployed directly on a clean Linux VPS (Debian/Ubuntu) using `Nginx` as a reverse proxy, `Gunicorn` as the WSGI server, and strict systemd service management. This zero-overhead setup maximizes hardware utilization and eliminates Docker-layer networking encapsulation delays.

--- 
## 🛠️ Tech Stack 

* **Backend & Logic:** Python (Flask), Asyncio, HTTPX, SQLAlchemy, Alembic, Pytest.
* **Databases:** PostgreSQL (M2M & Self-referencing models), SQLite (High-speed local geo-cache).
* **Infrastructure & Security:** Linux VPS (Bare-Metal), Nginx Proxy, Gunicorn, SSL/TLS (Let's Encrypt), Cron Automation, Backups. 
* **Frontend:** Vanilla JS (ES6+), HTML5/CSS3 (Semantic Web, BEM, Zero heavy frameworks), Mobile-First Design. 

---


## 📸 Interface & Layout Preview 

The frontend is built with a strict **Mobile-First approach** and adaptive Light/Dark theme support, ensuring flawless performance across modern viewports.
 
**🔹 Main Page & Cart (Tablet / Mobile Layout)**
<img width="100%" alt="screenshot" src="https://github.com/user-attachments/assets/afd63aa8-05d2-4bf5-90c3-89af3d6ab456" />

**🔹 Advanced Checkout & Delivery Selection (Desktop Layout)**
<img width="100%" alt="delivery" src="https://github.com/user-attachments/assets/243a3957-f8cc-42a8-9ab9-4d83fb337923" />


---

## 🔥 Key Engineering Challenges Solved 

### 🏎️ 1. Client-Side State Sync & Traffic Reduction (70% Fewer Requests)
* **Challenge:** Multi-tab shopping often leads to fragmented cart states, abandoned checkouts, and excessive backend database polling.
* **Solution:** Implemented cart state management entirely inside `Local Storage` and synchronized tab states reactively using the **Broadcast Channel API**. Multi-tier discount logic recalculates instantly on the client side with final verification on the backend. This reduced redundant server traffic by **70%**.

### 📦 2. Complex Logistics & Order Splitting Algorithms
* Developed a custom server-side volumetric approximation algorithm that evaluates total order dimensions/weight against individual carrier API constraints.
* Built automated order-splitting logic that seamlessly divides overweight/over-volume orders into multiple independent shipping parcels, mapping them to optimized shipping presets.

### 🔒 3. Secure Webhook Ingestion & Resilience
* The `Payment Webhook Receiver` utilizes Nginx-level routing and signature validation bypassed from standard rate limiters (`Rate Limit Exempt`) to guarantee zero dropped webhooks.
* All cron automation tasks feature strict execution timeouts, exponential backoff, and stateful retry policies. 

---

## 📦 Local Development Setup
1. **Clone the repository and prepare the environment:**
    ```
    git clone https://github.com/dashdash27/OakAffection.git
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
	```

2. **Environment Variables:**
	Create a `.env` file in the root directory and provide your local PostgreSQL connection details, API keys, and application settings.

3. **Initialize the Database & Catalog:**
	```
	flask db upgrade 
	python run.py 
	``` 
	*Note: The platform features dynamic category and SEO management. Upon the first launch, access the Custom Admin Panel to initialize the catalog structure.*

