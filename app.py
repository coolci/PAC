from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import logging
import math
from datetime import datetime
import os # Added for send_from_directory if needed, though static_folder handles it well

# Configure basic logging for the Flask app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'
)

app = Flask(__name__)
DB_FILE = "procurement_data.db"  # Ensure this matches the DB file used by crawler and db_setup

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # For dictionary-like row access
        # Foreign key pragma is good practice if you perform writes, though less critical for reads
        # conn.execute("PRAGMA foreign_keys = ON;") 
        logging.debug(f"Database connection established to {DB_FILE}.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {DB_FILE}: {e}", exc_info=True)
        # In a real app, you might want to raise a custom exception or handle this more gracefully
        raise  

@app.route('/')
def index():
    """A simple root route to confirm the server is running."""
    # return "Welcome to the Procurement Data API!" # Old root
    # Serve static files (index.html) from the 'static' directory
    # Flask's default static_url_path is '/static'.
    # send_from_directory will look in app.static_folder which is 'static' by default.
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """API endpoint to list all procurement categories."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category_code, path_name FROM categories ORDER BY name;")
        categories_rows = cursor.fetchall()
        
        # Convert sqlite3.Row objects to a list of dictionaries
        categories_list = [dict(row) for row in categories_rows]
        
        return jsonify(categories_list)
        
    except sqlite3.Error as e:
        logging.error(f"Database error in get_categories: {e}", exc_info=True)
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_categories: {e}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred."}), 500
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed for get_categories.")


def date_to_ms_timestamp(date_str):
    """Converts a YYYY-MM-DD date string to a millisecond Unix timestamp."""
    if not date_str:
        return None
    try:
        dt_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return int(dt_obj.timestamp() * 1000)
    except ValueError:
        logging.warning(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")
        return None

@app.route('/api/articles', methods=['GET'])
def search_articles():
    """API endpoint to search and list articles with pagination."""
    conn = None
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if page < 1: page = 1
        if per_page < 1: per_page = 10
        if per_page > 100: per_page = 100 # Max limit

        # Filter parameters
        title_keyword = request.args.get('title', type=str)
        category_id = request.args.get('category_id', type=int)
        project_name_keyword = request.args.get('project_name', type=str)
        purchase_name_keyword = request.args.get('purchase_name', type=str)
        district_name_keyword = request.args.get('district_name', type=str)
        procurement_method = request.args.get('procurement_method', type=str)
        
        publish_date_start_str = request.args.get('publish_date_start', type=str)
        publish_date_end_str = request.args.get('publish_date_end', type=str)
        publish_date_start_ts = date_to_ms_timestamp(publish_date_start_str)
        publish_date_end_ts = date_to_ms_timestamp(publish_date_end_str)
        # For end date, often want to include the whole day
        if publish_date_end_ts is not None:
            publish_date_end_ts += (24 * 60 * 60 * 1000 - 1) # End of the day

        budget_price_min = request.args.get('budget_price_min', type=float)
        budget_price_max = request.args.get('budget_price_max', type=float)
        
        supplier_name_keyword = request.args.get('supplier_name', type=str)
        total_contract_amount_min = request.args.get('total_contract_amount_min', type=float)
        total_contract_amount_max = request.args.get('total_contract_amount_max', type=float)

        bid_opening_time_start_str = request.args.get('bid_opening_time_start', type=str)
        bid_opening_time_end_str = request.args.get('bid_opening_time_end', type=str)
        bid_opening_time_start_ts = date_to_ms_timestamp(bid_opening_time_start_str)
        bid_opening_time_end_ts = date_to_ms_timestamp(bid_opening_time_end_str)
        if bid_opening_time_end_ts is not None:
            bid_opening_time_end_ts += (24 * 60 * 60 * 1000 - 1)


        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        base_query_fields = """
            SELECT id, article_api_id, category_id, title, author, publish_date, 
                   district_name, project_name, purchase_name, budget_price, 
                   procurement_method, supplier_name, total_contract_amount, 
                   bid_opening_time, attachment_count, crawl_timestamp 
            FROM articles
        """
        count_query_select = "SELECT COUNT(*) as total FROM articles"
        
        conditions = []
        params = []

        if title_keyword:
            conditions.append("LOWER(title) LIKE LOWER(?)") # Case-insensitive
            params.append(f"%{title_keyword}%")
        if category_id is not None:
            conditions.append("category_id = ?")
            params.append(category_id)
        if project_name_keyword:
            conditions.append("project_name LIKE ?")
            params.append(f"%{project_name_keyword}%")
        if purchase_name_keyword:
            conditions.append("LOWER(purchase_name) LIKE LOWER(?)") # Case-insensitive
            params.append(f"%{purchase_name_keyword}%")
        if district_name_keyword:
            conditions.append("LOWER(district_name) LIKE LOWER(?)") # Case-insensitive
            params.append(f"%{district_name_keyword}%")
        if procurement_method:
            conditions.append("LOWER(procurement_method) = LOWER(?)") # Case-insensitive for exact match
            params.append(procurement_method)
        
        if publish_date_start_ts is not None:
            conditions.append("publish_date >= ?")
            params.append(publish_date_start_ts)
        if publish_date_end_ts is not None:
            conditions.append("publish_date <= ?")
            params.append(publish_date_end_ts)

        if budget_price_min is not None:
            conditions.append("budget_price >= ?")
            params.append(budget_price_min)
        if budget_price_max is not None:
            conditions.append("budget_price <= ?")
            params.append(budget_price_max)

        if supplier_name_keyword:
            conditions.append("LOWER(supplier_name) LIKE LOWER(?)") # Case-insensitive
            params.append(f"%{supplier_name_keyword}%")
        if total_contract_amount_min is not None:
            conditions.append("total_contract_amount >= ?")
            params.append(total_contract_amount_min)
        if total_contract_amount_max is not None:
            conditions.append("total_contract_amount <= ?")
            params.append(total_contract_amount_max)

        if bid_opening_time_start_ts is not None:
            conditions.append("bid_opening_time >= ?")
            params.append(bid_opening_time_start_ts)
        if bid_opening_time_end_ts is not None:
            conditions.append("bid_opening_time <= ?")
            params.append(bid_opening_time_end_ts)

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # Execute count query
        full_count_query = count_query_select + where_clause
        logging.debug(f"Executing count query: {full_count_query} with params: {params}")
        cursor.execute(full_count_query, params)
        total_articles_row = cursor.fetchone()
        total_articles = total_articles_row['total'] if total_articles_row else 0
        total_pages = math.ceil(total_articles / per_page) if total_articles > 0 else 1


        # Execute main data query with pagination and ordering
        offset = (page - 1) * per_page
        main_query = base_query_fields + where_clause + " ORDER BY publish_date DESC LIMIT ? OFFSET ?"
        final_params = params + [per_page, offset]
        logging.debug(f"Executing main query: {main_query} with params: {final_params}")
        cursor.execute(main_query, final_params)
        articles_rows = cursor.fetchall()
        
        articles_list = [dict(row) for row in articles_rows]
        
        return jsonify({
            "data": articles_list,
            "page": page,
            "per_page": per_page,
            "total_articles": total_articles,
            "total_pages": total_pages
        })

    except sqlite3.Error as e:
        logging.error(f"Database error in search_articles: {e}", exc_info=True)
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        logging.error(f"Unexpected error in search_articles: {e}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred."}), 500
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed for search_articles.")

if __name__ == '__main__':
    # Note: debug=True is great for development but should be False in production.
    app.run(debug=True, port=5000)
