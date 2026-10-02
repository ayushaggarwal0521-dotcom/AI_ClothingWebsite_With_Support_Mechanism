# ATELIER 9 – AI clothing store

Run locally:
    pip install -r requirements.txt
    copy .env.example to .env and fill it in
    uvicorn app.main:app --reload
    open http://localhost:8000/store/

Layout:
    app/            FastAPI backend + services (+ storefront.py for cart / Buy Now)
    mcp_server/     MCP tools used by the AI assistant
    frontend/       the website (served at /store)
    dataset/raw/    product images (served at /images)
    data/           products.json
    scripts/        seed scripts (read DB password from env)
