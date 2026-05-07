# app/seed_db.py
from app.models.database import SessionLocal, Vecino

def register_me():
    db = SessionLocal()
    try:
        # Verificar si ya existe
        vecino = db.query(Vecino).filter(Vecino.telefono == "56981394911").first()
        
        if not vecino:
            nuevo_vecino = Vecino(
                nombre="Jaime Campillay",
                telefono="56981394911",
                activo=True
            )
            db.add(nuevo_vecino)
            db.commit()
            print("✅ Vecino registrado con éxito.")
        else:
            vecino.activo = True
            db.commit()
            print("ℹ️ El vecino ya existía. Se ha asegurado que esté activo.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    register_me()