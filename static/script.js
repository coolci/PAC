document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const resetButton = document.getElementById('resetButton');
    const categorySelect = document.getElementById('category');
    const resultsBody = document.getElementById('resultsBody');
    const prevPageButton = document.getElementById('prevPage');
    const nextPageButton = document.getElementById('nextPage');
    const pageInfoSpan = document.getElementById('pageInfo');

    let currentPage = 1;
    const articlesPerPage = 20; // Should match API default or be a user choice
    let categoriesMap = {}; // To store category_id -> name mapping
    let currentSearchFilters = {}; // To store current filters for pagination

    // --- Initialization ---

    async function initializePage() {
        await fetchAndPopulateCategories(); // Fetch categories first
        await fetchArticles(); // Then fetch initial articles
    }

    // --- Category Handling ---

    async function fetchAndPopulateCategories() {
        try {
            const response = await fetch('/api/categories');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const categories = await response.json();
            
            categoriesMap = {}; // Reset map
            categorySelect.innerHTML = '<option value="">All Categories</option>'; // Reset options

            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
                categoriesMap[category.id] = category.name; // Populate map
            });
            console.log("Categories loaded and populated.", categoriesMap);
        } catch (error) {
            console.error('Error fetching categories:', error);
            // Optionally display an error message to the user
        }
    }

    // --- Article Fetching and Display ---

    function collectFilters() {
        const formData = new FormData(searchForm);
        const filters = {};
        for (const [key, value] of formData.entries()) {
            if (value) { // Only include parameters that have a value
                filters[key] = value;
            }
        }
        return filters;
    }

    async function fetchArticles(page = 1) {
        currentPage = page;
        currentSearchFilters = collectFilters(); // Update current filters
        
        const params = new URLSearchParams(currentSearchFilters);
        params.append('page', currentPage);
        params.append('per_page', articlesPerPage);

        const url = `/api/articles?${params.toString()}`;
        console.log(`Fetching articles from: ${url}`);

        try {
            const response = await fetch(url);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: "Failed to parse error response" }));
                throw new Error(`HTTP error! status: ${response.status} - ${errorData.error || response.statusText}`);
            }
            const apiResponse = await response.json();
            displayResults(apiResponse.data);
            updatePaginationControls(apiResponse);
        } catch (error) {
            console.error('Error fetching articles:', error);
            resultsBody.innerHTML = `<tr><td colspan="7">Error loading articles: ${error.message}</td></tr>`;
            // Reset pagination display on error
            pageInfoSpan.textContent = 'Page 1 of 1';
            prevPageButton.disabled = true;
            nextPageButton.disabled = true;
        }
    }

    function displayResults(articles) {
        resultsBody.innerHTML = ''; // Clear previous results

        if (!articles || articles.length === 0) {
            resultsBody.innerHTML = '<tr><td colspan="7">No articles found.</td></tr>';
            return;
        }

        articles.forEach(article => {
            const row = resultsBody.insertRow();
            
            const titleCell = row.insertCell();
            titleCell.textContent = article.title || 'N/A';

            const categoryCell = row.insertCell();
            categoryCell.textContent = categoriesMap[article.category_id] || 'Unknown';
            
            const publishDateCell = row.insertCell();
            publishDateCell.textContent = article.publish_date 
                ? new Date(article.publish_date).toLocaleDateString('en-CA') 
                : 'N/A';
            
            row.insertCell().textContent = article.project_name || 'N/A';
            row.insertCell().textContent = article.purchase_name || 'N/A';
            row.insertCell().textContent = article.district_name || 'N/A';
            
            const budgetCell = row.insertCell();
            budgetCell.textContent = article.budget_price !== null && article.budget_price !== undefined 
                ? parseFloat(article.budget_price).toFixed(2) 
                : 'N/A';
        });
    }

    // --- Pagination Controls ---

    function updatePaginationControls(apiResponse) {
        pageInfoSpan.textContent = `Page ${apiResponse.page} of ${apiResponse.total_pages}`;
        prevPageButton.disabled = apiResponse.page <= 1;
        nextPageButton.disabled = apiResponse.page >= apiResponse.total_pages;
    }

    prevPageButton.addEventListener('click', () => {
        if (currentPage > 1) {
            fetchArticles(currentPage - 1);
        }
    });

    nextPageButton.addEventListener('click', () => {
        // Assuming total_pages is correctly updated by updatePaginationControls
        // We might need to store total_pages globally if nextPageButton can be clicked before apiResponse is processed.
        // For now, this relies on the button's disabled state being accurate.
        fetchArticles(currentPage + 1);
    });

    // --- Event Listeners ---

    searchForm.addEventListener('submit', (event) => {
        event.preventDefault(); // Prevent default form submission
        fetchArticles(1); // Fetch first page with new filters
    });

    resetButton.addEventListener('click', () => {
        searchForm.reset();
        // categorySelect.value = ""; // Ensure category is reset if not part of form.reset() behavior for selects
        fetchArticles(1); // Fetch first page with no filters
    });

    // --- Initial Load ---
    initializePage();
});
