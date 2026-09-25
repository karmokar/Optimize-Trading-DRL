from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from phase7_hybrid_veto import run_hybrid_veto_system

from Nifity50service import router as nifty_router
app = FastAPI(title="DRL Portfolio AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,   # fixed: was allow_crendentials
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nifty_router)

@app.get("/api/v1/generate-portfolio")
async def generate_portfolio():
    try:
        # Run the existing pipeline with automatic veto enabled
        result = run_hybrid_veto_system()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)