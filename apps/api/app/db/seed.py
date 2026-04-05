from app.db.session import SessionLocal
from app.services.seed import seed_database


def main() -> None:
    with SessionLocal() as session:
        seed_database(session)
    print("Seeded AegisCore development data.")


if __name__ == "__main__":
    main()

