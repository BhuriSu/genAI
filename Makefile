up: 
	docker compose --env-file .env up --build -d

etl: 
	docker exec etl python pipeline/main_pipeline.py


pytest:
	docker exec etl python -m pytest -p no:warnings -v


format:
	docker exec etl python -m black -S --line-length 79 .


isort:
	docker exec etl isort .


type:
	docker exec etl mypy --ignore-missing-imports .


lint: 
	docker exec etl flake8 .


ci: isort format type lint pytest


warehouse: 
	winpty docker exec -ti warehouse psql mysql://root:Testmysql111@localhost:3306/game_sales

down: 
	docker compose down 