from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def health_check():
	return {"message": "Recommend router is available"}
