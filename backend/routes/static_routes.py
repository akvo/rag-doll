import json

from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse


router = APIRouter()

POLICY_FILE_PATH = "./sources/static/data-retention-policy.json"


@router.get("/data-retention-policy")
def get_policy_json():
    try:
        with open(POLICY_FILE_PATH, "r") as file:
            policy_data = json.load(file)
        return JSONResponse(content=policy_data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Policy file not found")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, detail="Error decoding policy JSON"
        )
