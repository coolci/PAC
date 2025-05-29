import requests
import json
import time
import logging
import sqlite3

# Configure basic logging at the module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'
)

DB_FILE = "procurement_data.db"  # Database file name

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

BASE_URL = "https://zfcg.czt.zj.gov.cn"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # For dictionary-like row access
        conn.execute("PRAGMA foreign_keys = ON;") # Ensure foreign key constraints are active
        logging.debug(f"Database connection established to {DB_FILE}.")
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {DB_FILE}: {e}", exc_info=True)
        raise
    return conn

def fetch_procurement_categories():
    """
    Fetches procurement categories from the API and stores them in the database.
    Returns a list of category details, including their database IDs.
    """
    categories_url = f"{BASE_URL}/admin/category/home/categoryTreeFind"
    params = {
        "parentId": "600007",
        "siteId": "110"
    }
    logging.info(f"Fetching procurement categories from {categories_url} with params: {params}")
    
    api_categories_data = [] # Raw data from API to be processed for DB
    db_categories_with_ids = [] # Final list of dicts including DB ID

    try:
        response = requests.get(categories_url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        def parse_api_categories_recursive(nodes, current_path_parts):
            for node in nodes:
                name = node.get('name')
                if not name:
                    logging.debug(f"Skipping node without a name: {node}")
                    continue
                
                new_path_parts = current_path_parts + [name]
                category_code_from_api = node.get('code')
                api_node_id = node.get('id') # This is 'source_id'
                api_parent_id = node.get('parentId') # This is 'parent_source_id'

                # Condition to identify a target category (e.g., starts with "110-")
                if category_code_from_api and category_code_from_api.startswith("110-"):
                    path_name_constructed = "/" + "/".join(new_path_parts)
                    api_categories_data.append({
                        "name": name,
                        "category_code": category_code_from_api,
                        "path_name": path_name_constructed,
                        "source_id": api_node_id,
                        "parent_source_id": api_parent_id
                    })
                
                if node.get('children') and len(node.get('children')) > 0:
                    parse_api_categories_recursive(node.get('children'), new_path_parts)
        
        if data and isinstance(data, dict) and \
           'result' in data and isinstance(data['result'], dict) and \
           'data' in data['result'] and isinstance(data['result']['data'], list):
            parse_api_categories_recursive(data['result']['data'], [])
            logging.info(f"Successfully fetched {len(api_categories_data)} categories from API.")
        else:
            logging.error(f"Unexpected data format from category API. Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return []

        if api_categories_data:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for cat_api_data in api_categories_data:
                    try:
                        sql = """INSERT OR IGNORE INTO categories (name, category_code, path_name, source_id, parent_source_id)
                                 VALUES (?, ?, ?, ?, ?)"""
                        cursor.execute(sql, (
                            cat_api_data['name'], 
                            cat_api_data['category_code'], 
                            cat_api_data['path_name'],
                            cat_api_data.get('source_id'),
                            cat_api_data.get('parent_source_id')
                        ))
                        
                        # Fetch the DB ID. If IGNORE'd, it already exists.
                        cursor.execute("SELECT id, name, category_code, path_name FROM categories WHERE category_code = ?", 
                                       (cat_api_data['category_code'],))
                        db_row = cursor.fetchone()
                        if db_row:
                            # Convert sqlite3.Row to a standard dict for consistent return type
                            db_categories_with_ids.append(dict(db_row)) 
                        else:
                            logging.warning(f"Could not retrieve category from DB after insert/ignore: {cat_api_data['category_code']}")
                    except sqlite3.Error as db_e:
                        logging.error(f"SQLite error processing category {cat_api_data['category_code']}: {db_e}", exc_info=True)
                conn.commit()
            logging.info(f"Processed {len(api_categories_data)} API categories into DB. Returning {len(db_categories_with_ids)} categories with DB IDs.")
            
    except requests.exceptions.Timeout:
        logging.error(f"Timeout while fetching categories from {categories_url}.")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error {e.response.status_code} while fetching categories from {categories_url}. Response: {e.response.text[:200]}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error while fetching categories from {categories_url}: {e}")
    except json.JSONDecodeError as e:
        response_text = response.text[:200] if 'response' in locals() and hasattr(response, 'text') else "N/A"
        logging.error(f"Error parsing JSON response for categories from {categories_url}. Error: {e}. Response text: {response_text}")
    except Exception: # Catch any other unexpected error
        logging.exception(f"An unexpected error occurred in fetch_procurement_categories for {categories_url}")
        
    return db_categories_with_ids


def fetch_articles_for_category(category_details, max_pages=None):
    articles_url = f"{BASE_URL}/portal/category"
    all_articles = []
    page_no = 1
    category_code = category_details.get('category_code', 'N/A') # Use 'category_code' from dict
    category_display_name = category_details.get('name', category_code)
    
    logging.info(f"Fetching articles for category '{category_display_name}' (Code: {category_code}), max_pages={max_pages}")

    with requests.Session() as session:
        while True:
            post_data = {
                "pageNo": page_no, "pageSize": 15, "categoryCode": category_code,
                "isGov": True, "excludeDistrictPrefix": ["90", "006011"],
                "_t": int(time.time() * 1000), "isProvince": True 
            }
            if 'path_name' in category_details and category_details['path_name']: # Use 'path_name'
                 post_data['pathName'] = category_details['path_name']
            
            logging.debug(f"Fetching page {page_no} for category '{category_display_name}'. POST data: {post_data}")
            
            try:
                response = session.post(articles_url, json=post_data, headers=HEADERS, timeout=20)
                response.raise_for_status()
                response_data = response.json()
                
                if not response_data.get('success'):
                    error_detail = response_data.get('error', {})
                    error_msg = error_detail.get('message', 'Unknown API error') if isinstance(error_detail, dict) else str(error_detail)
                    logging.warning(f"API reported failure for page {page_no}, category '{category_display_name}'. Error: {error_msg}. POST data: {post_data}")
                    break

                article_list_container = response_data.get('result', {}).get('data', {})
                if not isinstance(article_list_container, dict):
                    logging.error(f"article_list_container is not a dictionary for page {page_no}, category '{category_display_name}'. Value: {article_list_container}")
                    break

                articles_on_page = article_list_container.get('records', article_list_container.get('data'))

                if articles_on_page is None:
                    logging.warning(f"Could not find article list in response for page {page_no}, category '{category_display_name}'. Container: {article_list_container}")
                    break
                
                if not articles_on_page: # Empty list means no more articles or none on first page
                    logging.info(f"No {'more ' if page_no > 1 else ''}articles found on page {page_no} for category '{category_display_name}'.")
                    break

                for article_raw in articles_on_page:
                    all_articles.append({
                        "articleId": article_raw.get('articleId'), "title": article_raw.get('title'),
                        "publishDate": article_raw.get('publishDate'), "districtName": article_raw.get('districtName'),
                        "projectName": article_raw.get('projectName'), "purchaseName": article_raw.get('purchaseName'),
                        "budgetPrice": article_raw.get('budgetPrice')
                    })
                
                current_page_num = article_list_container.get('current', page_no)
                total_articles = article_list_container.get('total', 0)
                page_size = article_list_container.get('size', post_data['pageSize'])
                total_pages = article_list_container.get('pages', (total_articles + page_size - 1) // page_size if page_size else 0)

                logging.info(f"Page {current_page_num}/{total_pages} fetched for '{category_display_name}', {len(articles_on_page)} articles on this page. Total articles for category: {total_articles}")

                if max_pages and current_page_num >= max_pages:
                    logging.info(f"Reached max_pages limit ({max_pages}) for category '{category_display_name}'.")
                    break
                if current_page_num >= total_pages:
                    logging.info(f"Fetched all available pages ({total_pages}) for category '{category_display_name}'.")
                    break
                page_no = current_page_num + 1
                time.sleep(1) 
            except requests.exceptions.Timeout:
                logging.error(f"Timeout fetching articles page {page_no} for category '{category_display_name}'.")
                break 
            except requests.exceptions.HTTPError as e:
                logging.error(f"HTTP error {e.response.status_code} fetching articles (page {page_no}, cat '{category_display_name}'). Resp: {e.response.text[:200]}")
                break
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error fetching articles (page {page_no}, cat '{category_display_name}'): {e}")
                break 
            except json.JSONDecodeError as e:
                response_text = response.text[:200] if 'response' in locals() and hasattr(response, 'text') else "N/A"
                logging.error(f"JSON error for articles (page {page_no}, cat '{category_display_name}'). Err: {e}. Resp: {response_text}")
                break
            except Exception:
                logging.exception(f"Unexpected error on page {page_no} for category '{category_display_name}'")
                break
    logging.info(f"Fetched {len(all_articles)} articles in total for category '{category_display_name}'.")
    return all_articles

def fetch_article_detail(article_id):
    if not article_id:
        logging.warning("fetch_article_detail called with no article_id.")
        return None
        
    detail_url = f"{BASE_URL}/portal/detail"
    params = {"articleId": article_id, "timestamp": int(time.time() * 1000)}
    logging.info(f"Fetching detail for article ID: {article_id} from {detail_url}")
    try:
        with requests.Session() as session: # New session for each detail fetch
            session.headers.update(HEADERS)
            response = session.get(detail_url, params=params, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            if not response_data.get('success'):
                error_detail = response_data.get('error', {})
                error_msg = error_detail.get('message', 'Unknown API error') if isinstance(error_detail, dict) else str(error_detail)
                logging.warning(f"API failure for article detail ID '{article_id}'. Error: {error_msg}")
                return None

            article_data_container = response_data.get('result')
            article_data = article_data_container.get('data') if isinstance(article_data_container, dict) and 'data' in article_data_container else article_data_container
            
            if not isinstance(article_data, dict):
                logging.error(f"No valid dict data in article detail for ID '{article_id}'. Data: {json.dumps(article_data, ensure_ascii=False, indent=2)}")
                return None

            detail = {
                "articleId": article_id, "title": article_data.get('title'),
                "author": article_data.get('author'), "publishDate": article_data.get('publishDate'),
                "htmlContent": article_data.get('htmlContent', article_data.get('content')),
                "textContent": article_data.get('textContent'), "attachmentCount": article_data.get('attachmentCount'),
                "districtName": article_data.get('districtName'), "projectName": article_data.get('projectName'),
                "purchaseName": article_data.get('purchaseName'), "budgetPrice": article_data.get('budgetPrice'),
                "procurementMethod": article_data.get('procurementMethod'),
                # Fields from API case study that might be in article_data directly
                "supplierName": article_data.get('supplierName'), 
                "totalContractAmount": article_data.get('totalContractAmount'),
                "bidOpeningTime": article_data.get('bidOpeningTime')
            }
            logging.info(f"Successfully fetched details for article ID: {article_id}")
            return detail
    except requests.exceptions.Timeout:
        logging.error(f"Timeout fetching detail for ID '{article_id}'.")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error {e.response.status_code} fetching detail for ID '{article_id}'. Resp: {e.response.text[:200]}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error fetching detail for ID '{article_id}': {e}")
    except json.JSONDecodeError as e:
        response_text = response.text[:200] if 'response' in locals() and hasattr(response, 'text') else "N/A"
        logging.error(f"JSON error for detail ID '{article_id}'. Err: {e}. Resp: {response_text}")
    except Exception:
        logging.exception(f"Unexpected error fetching detail for ID '{article_id}'")
    return None

def run_crawler(max_categories=None, max_articles_per_category=None, max_pages_per_category=None):
    logging.info(f"Starting crawler run. Limits: cats={max_categories}, articles/cat={max_articles_per_category}, pages/cat={max_pages_per_category}")
    categories_processed = 0
    articles_considered_total = 0
    details_fetched_successful = 0
    articles_saved_total = 0

    all_db_categories = fetch_procurement_categories()

    if not all_db_categories:
        logging.warning("No procurement categories fetched or resolved from DB. Exiting crawler.")
        return

    logging.info(f"Found {len(all_db_categories)} total categories in DB to process.")

    for category_index, category_db_data in enumerate(all_db_categories):
        if max_categories and categories_processed >= max_categories:
            logging.info(f"Reached max_categories limit ({max_categories}). Stopping.")
            break
        
        category_name = category_db_data.get('name', 'Unknown Category')
        category_id_db = category_db_data.get('id') # DB ID
        logging.info(f"Processing category {category_index + 1}/{len(all_db_categories)}: '{category_name}' (DB ID: {category_id_db})")

        # Pass the full category dict from DB (which includes name, category_code, path_name)
        articles_from_api_list = fetch_articles_for_category(
            category_db_data, 
            max_pages=max_pages_per_category
        )
        categories_processed += 1
        
        if articles_from_api_list:
            num_articles_listed = len(articles_from_api_list)
            logging.info(f"Found {num_articles_listed} articles in API list for category '{category_name}'.")
            
            articles_to_process_details = articles_from_api_list
            if max_articles_per_category is not None:
                articles_to_process_details = articles_from_api_list[:max_articles_per_category]
                if len(articles_to_process_details) < num_articles_listed:
                    logging.info(f"Limiting detail processing to {len(articles_to_process_details)} articles for '{category_name}'.")

            cat_details_fetched = 0
            cat_articles_saved = 0
            articles_considered_total += len(articles_to_process_details)

            for list_item_idx, article_list_item_data in enumerate(articles_to_process_details):
                api_article_id = article_list_item_data.get('articleId')
                list_title = article_list_item_data.get('title', 'No Title')

                if not api_article_id:
                    logging.warning(f"Skipping article with missing 'articleId' in list view for '{category_name}'. Data: {article_list_item_data}")
                    continue

                logging.info(f"  Processing article {list_item_idx + 1}/{len(articles_to_process_details)}: '{list_title}' (API ID: {api_article_id})")
                
                detail_data = fetch_article_detail(api_article_id)
                
                if detail_data:
                    details_fetched_successful += 1
                    cat_details_fetched +=1

                # Combine: Start with list data, update with detail data if detail exists
                # Prioritize non-None values from list if detail has None for that specific field
                combined_data = {**article_list_item_data, **(detail_data if detail_data else {})}
                for key, value in article_list_item_data.items():
                    if value is not None and combined_data.get(key) is None:
                        combined_data[key] = value
                
                # Prepare for DB
                db_tuple = (
                    api_article_id, category_id_db, combined_data.get('title'), combined_data.get('author'),
                    combined_data.get('publishDate'), combined_data.get('districtName'), combined_data.get('projectName'),
                    combined_data.get('purchaseName'), combined_data.get('budgetPrice'), combined_data.get('procurementMethod'),
                    combined_data.get('supplierName'), combined_data.get('totalContractAmount'), combined_data.get('bidOpeningTime'),
                    combined_data.get('htmlContent'), combined_data.get('textContent'), combined_data.get('attachmentCount'),
                    int(time.time()) # crawl_timestamp
                )

                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        sql_upsert = """
                        INSERT INTO articles (
                            article_api_id, category_id, title, author, publish_date,
                            district_name, project_name, purchase_name, budget_price,
                            procurement_method, supplier_name, total_contract_amount,
                            bid_opening_time, html_content, text_content,
                            attachment_count, crawl_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(article_api_id) DO UPDATE SET
                            title=excluded.title, author=excluded.author, publish_date=excluded.publish_date,
                            district_name=excluded.district_name, project_name=excluded.project_name,
                            purchase_name=excluded.purchase_name, budget_price=excluded.budget_price,
                            procurement_method=excluded.procurement_method, supplier_name=excluded.supplier_name,
                            total_contract_amount=excluded.total_contract_amount, bid_opening_time=excluded.bid_opening_time,
                            html_content=excluded.html_content, text_content=excluded.text_content,
                            attachment_count=excluded.attachment_count, crawl_timestamp=excluded.crawl_timestamp,
                            category_id=excluded.category_id;
                        """
                        cursor.execute(sql_upsert, db_tuple)
                        conn.commit()
                        articles_saved_total += 1
                        cat_articles_saved += 1
                        logging.info(f"    Saved article '{combined_data.get('title', 'N/A')}' (API ID: {api_article_id}) to DB.")
                except sqlite3.Error as db_e:
                    logging.error(f"    DB error saving article API ID {api_article_id}: {db_e}", exc_info=True)
                except Exception:
                    logging.exception(f"    Unexpected error saving article API ID {api_article_id}")

                if detail_data: # Only sleep if a detail API call was made
                    time.sleep(0.5) 
            
            logging.info(f"Finished category '{category_name}'. Articles considered: {len(articles_to_process_details)}. Details successfully fetched: {cat_details_fetched}. Articles saved/updated in DB: {cat_articles_saved}.")
        else:
            logging.info(f"No articles listed for category '{category_name}'.")

    logging.info("Crawler run finished.")
    logging.info("--------------------SUMMARY--------------------")
    logging.info(f"Total categories processed: {categories_processed}")
    logging.info(f"Total articles considered from lists (respecting limits): {articles_considered_total}") 
    logging.info(f"Total article details fetched successfully: {details_fetched_successful}")
    logging.info(f"Total articles saved/updated in database: {articles_saved_total}")
    logging.info("-----------------------------------------------")

if __name__ == "__main__":
    # Configure logging (if not already configured at module level, though it is in this script)
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
    
    logging.info("Starting a new crawl session.")
    # Ensure db_setup.py has been run once to create the database and tables.
    # To perform a full crawl, ensure all limits are set to None.
    # This will iterate through all categories, all pages for each category,
    # and process all articles found.
    # This process can take a very significant amount of time (hours or even days)
    # depending on the number of categories, articles, pages, and server responsiveness.
    # Monitor the log output for progress.
    
    run_crawler(max_categories=None, max_articles_per_category=None, max_pages_per_category=None)

    logging.info("Full crawl process initiated (or completed if it finished quickly).")

# To run the full crawl:
# 1. Ensure the database schema is initialized by running `python db_setup.py` once.
# 2. Execute this script from your terminal: `python crawler.py`
# 3. Monitor the console output for logs. The process will populate `procurement_data.db`.
#    It is expected to take a very long time.
