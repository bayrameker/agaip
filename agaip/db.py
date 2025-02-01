# agaip/db.py
from tortoise import Tortoise

async def init_db(config_path: str = "config.yaml"):
    # Gerekirse config dosyasından db_url alınabilir.
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['agaip.models.task']},
    )
    await Tortoise.generate_schemas()

async def close_db():
    await Tortoise.close_connections()
