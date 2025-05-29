import sqlite3
import logging

# Configure basic logging for this script
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'
)

DB_FILE = "procurement_data.db"

def create_connection(db_file):
    """Create a database connection to a SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # Enable foreign key constraint enforcement
        conn.execute("PRAGMA foreign_keys = ON;")
        logging.info(f"Successfully connected to database: {db_file} (SQLite version: {sqlite3.sqlite_version})")
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {db_file}: {e}")
    return conn

def create_table(conn, create_table_sql):
    """Create a table from the create_table_sql statement."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        logging.info(f"Successfully executed SQL: {create_table_sql.splitlines()[0]}...") # Log first line
    except sqlite3.Error as e:
        logging.error(f"Error creating table with SQL '{create_table_sql.splitlines()[0]}...': {e}")

def create_index(conn, create_index_sql):
    """Create an index from the create_index_sql statement."""
    try:
        c = conn.cursor()
        c.execute(create_index_sql)
        logging.info(f"Successfully executed SQL: {create_index_sql}")
    except sqlite3.Error as e:
        logging.error(f"Error creating index with SQL '{create_index_sql}': {e}")

def initialize_database(db_file):
    """Orchestrate the database setup: create tables and indexes."""
    logging.info(f"Initializing database: {db_file}")

    sql_create_categories_table = """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_code TEXT NOT NULL UNIQUE,
        path_name TEXT,
        source_id INTEGER,
        parent_source_id INTEGER
    );
    """

    sql_create_articles_table = """
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_api_id TEXT NOT NULL UNIQUE,
        category_id INTEGER NOT NULL,
        title TEXT,
        author TEXT,
        publish_date INTEGER,
        district_name TEXT,
        project_name TEXT,
        purchase_name TEXT,
        budget_price REAL,
        procurement_method TEXT,
        supplier_name TEXT,
        total_contract_amount REAL,
        bid_opening_time INTEGER,
        html_content TEXT,
        text_content TEXT,
        attachment_count INTEGER,
        crawl_timestamp INTEGER NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    );
    """
    
    category_indexes = [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_cat_category_code ON categories(category_code);",
        "CREATE INDEX IF NOT EXISTS idx_cat_name ON categories(name);"
    ]

    article_indexes = [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_art_article_api_id ON articles(article_api_id);",
        "CREATE INDEX IF NOT EXISTS idx_art_category_id ON articles(category_id);",
        "CREATE INDEX IF NOT EXISTS idx_art_title ON articles(title);",
        "CREATE INDEX IF NOT EXISTS idx_art_publish_date ON articles(publish_date);",
        "CREATE INDEX IF NOT EXISTS idx_art_district_name ON articles(district_name);",
        "CREATE INDEX IF NOT EXISTS idx_art_project_name ON articles(project_name);",
        "CREATE INDEX IF NOT EXISTS idx_art_purchase_name ON articles(purchase_name);",
        "CREATE INDEX IF NOT EXISTS idx_art_procurement_method ON articles(procurement_method);",
        "CREATE INDEX IF NOT EXISTS idx_art_supplier_name ON articles(supplier_name);",
        "CREATE INDEX IF NOT EXISTS idx_art_budget_price ON articles(budget_price);",
        "CREATE INDEX IF NOT EXISTS idx_art_total_contract_amount ON articles(total_contract_amount);"
    ]

    conn = create_connection(db_file)

    if conn is not None:
        logging.info("Creating tables...")
        create_table(conn, sql_create_categories_table)
        create_table(conn, sql_create_articles_table)
        
        logging.info("Creating indexes for 'categories' table...")
        for index_sql in category_indexes:
            create_index(conn, index_sql)
            
        logging.info("Creating indexes for 'articles' table...")
        for index_sql in article_indexes:
            create_index(conn, index_sql)
            
        conn.close()
        logging.info(f"Database initialization complete for {db_file}.")
    else:
        logging.error(f"Database initialization failed for {db_file}: Could not create connection.")

if __name__ == '__main__':
    initialize_database(DB_FILE)
