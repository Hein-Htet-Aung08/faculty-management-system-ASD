from database import initialize_database, table_counts


if __name__ == "__main__":
    initialize_database(seed=True)
    for table, count in table_counts().items():
        print(f"{table}: {count} records")
