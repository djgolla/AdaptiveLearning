setup:

main backend:
1) create/activate venv
2) pip install -r requirements.txt
3) uvicorn main:app --reload --port 8000

facial sidecar (older python (3.9), separate venv):
1) open a second terminal
2) activate your older-python venv
3) pip install -r facial/requirements.txt
4) set a non-conflicting port (default is 8002)
5) run facial service:
	- python facial/stress_api.py



