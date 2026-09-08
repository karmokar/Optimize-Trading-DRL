from fastapi import FastAPI, HTTPException
from phase7_hybrid_veto import run_hybrid_veto_system

app = FastAPI(title="DRL Portfolio AI Engine")

@app.get("/api/v1/generate-portfolio")
async def generate_portfolio():
    try:
        # Run the existing pipeline with automatic veto enabled
        result = run_hybrid_veto_system(auto_veto=True)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))