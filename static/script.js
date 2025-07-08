const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000' 
    : 'https://price-scope-liart.vercel.app';

// Function to get flag emoji from country code
function getFlagEmoji(countryCode) {
    const codePoints = countryCode
        .toUpperCase()
        .split('')
        .map(char => 127397 + char.charCodeAt());
    return String.fromCodePoint(...codePoints);
}

// Countries data embedded directly to avoid CORS issues
const countries = [
    {"name": "Afghanistan", "code": "AF"},
    {"name": "Albania", "code": "AL"},
    {"name": "Algeria", "code": "DZ"},
    {"name": "Andorra", "code": "AD"},
    {"name": "Angola", "code": "AO"},
    {"name": "Antigua and Barbuda", "code": "AG"},
    {"name": "Argentina", "code": "AR"},
    {"name": "Armenia", "code": "AM"},
    {"name": "Australia", "code": "AU"},
    {"name": "Austria", "code": "AT"},
    {"name": "Azerbaijan", "code": "AZ"},
    {"name": "Bahamas", "code": "BS"},
    {"name": "Bahrain", "code": "BH"},
    {"name": "Bangladesh", "code": "BD"},
    {"name": "Barbados", "code": "BB"},
    {"name": "Belarus", "code": "BY"},
    {"name": "Belgium", "code": "BE"},
    {"name": "Belize", "code": "BZ"},
    {"name": "Benin", "code": "BJ"},
    {"name": "Bhutan", "code": "BT"},
    {"name": "Bolivia", "code": "BO"},
    {"name": "Bosnia and Herzegovina", "code": "BA"},
    {"name": "Botswana", "code": "BW"},
    {"name": "Brazil", "code": "BR"},
    {"name": "Brunei", "code": "BN"},
    {"name": "Bulgaria", "code": "BG"},
    {"name": "Burkina Faso", "code": "BF"},
    {"name": "Burundi", "code": "BI"},
    {"name": "Cambodia", "code": "KH"},
    {"name": "Cameroon", "code": "CM"},
    {"name": "Canada", "code": "CA"},
    {"name": "Cape Verde", "code": "CV"},
    {"name": "Central African Republic", "code": "CF"},
    {"name": "Chad", "code": "TD"},
    {"name": "Chile", "code": "CL"},
    {"name": "China", "code": "CN"},
    {"name": "Colombia", "code": "CO"},
    {"name": "Comoros", "code": "KM"},
    {"name": "Congo", "code": "CG"},
    {"name": "Costa Rica", "code": "CR"},
    {"name": "Croatia", "code": "HR"},
    {"name": "Cuba", "code": "CU"},
    {"name": "Cyprus", "code": "CY"},
    {"name": "Czech Republic", "code": "CZ"},
    {"name": "Denmark", "code": "DK"},
    {"name": "Djibouti", "code": "DJ"},
    {"name": "Dominica", "code": "DM"},
    {"name": "Dominican Republic", "code": "DO"},
    {"name": "Ecuador", "code": "EC"},
    {"name": "Egypt", "code": "EG"},
    {"name": "El Salvador", "code": "SV"},
    {"name": "Equatorial Guinea", "code": "GQ"},
    {"name": "Eritrea", "code": "ER"},
    {"name": "Estonia", "code": "EE"},
    {"name": "Ethiopia", "code": "ET"},
    {"name": "Fiji", "code": "FJ"},
    {"name": "Finland", "code": "FI"},
    {"name": "France", "code": "FR"},
    {"name": "Gabon", "code": "GA"},
    {"name": "Gambia", "code": "GM"},
    {"name": "Georgia", "code": "GE"},
    {"name": "Germany", "code": "DE"},
    {"name": "Ghana", "code": "GH"},
    {"name": "Greece", "code": "GR"},
    {"name": "Grenada", "code": "GD"},
    {"name": "Guatemala", "code": "GT"},
    {"name": "Guinea", "code": "GN"},
    {"name": "Guinea-Bissau", "code": "GW"},
    {"name": "Guyana", "code": "GY"},
    {"name": "Haiti", "code": "HT"},
    {"name": "Honduras", "code": "HN"},
    {"name": "Hong Kong", "code": "HK"},
    {"name": "Hungary", "code": "HU"},
    {"name": "Iceland", "code": "IS"},
    {"name": "India", "code": "IN"},
    {"name": "Indonesia", "code": "ID"},
    {"name": "Iran", "code": "IR"},
    {"name": "Iraq", "code": "IQ"},
    {"name": "Ireland", "code": "IE"},
    {"name": "Israel", "code": "IL"},
    {"name": "Italy", "code": "IT"},
    {"name": "Jamaica", "code": "JM"},
    {"name": "Japan", "code": "JP"},
    {"name": "Jordan", "code": "JO"},
    {"name": "Kazakhstan", "code": "KZ"},
    {"name": "Kenya", "code": "KE"},
    {"name": "Kiribati", "code": "KI"},
    {"name": "North Korea", "code": "KP"},
    {"name": "South Korea", "code": "KR"},
    {"name": "Kuwait", "code": "KW"},
    {"name": "Kyrgyzstan", "code": "KG"},
    {"name": "Laos", "code": "LA"},
    {"name": "Latvia", "code": "LV"},
    {"name": "Lebanon", "code": "LB"},
    {"name": "Lesotho", "code": "LS"},
    {"name": "Liberia", "code": "LR"},
    {"name": "Libya", "code": "LY"},
    {"name": "Liechtenstein", "code": "LI"},
    {"name": "Lithuania", "code": "LT"},
    {"name": "Luxembourg", "code": "LU"},
    {"name": "Macau", "code": "MO"},
    {"name": "Madagascar", "code": "MG"},
    {"name": "Malawi", "code": "MW"},
    {"name": "Malaysia", "code": "MY"},
    {"name": "Maldives", "code": "MV"},
    {"name": "Mali", "code": "ML"},
    {"name": "Malta", "code": "MT"},
    {"name": "Marshall Islands", "code": "MH"},
    {"name": "Mauritania", "code": "MR"},
    {"name": "Mauritius", "code": "MU"},
    {"name": "Mexico", "code": "MX"},
    {"name": "Micronesia", "code": "FM"},
    {"name": "Moldova", "code": "MD"},
    {"name": "Monaco", "code": "MC"},
    {"name": "Mongolia", "code": "MN"},
    {"name": "Montenegro", "code": "ME"},
    {"name": "Morocco", "code": "MA"},
    {"name": "Mozambique", "code": "MZ"},
    {"name": "Myanmar", "code": "MM"},
    {"name": "Namibia", "code": "NA"},
    {"name": "Nauru", "code": "NR"},
    {"name": "Nepal", "code": "NP"},
    {"name": "Netherlands", "code": "NL"},
    {"name": "New Zealand", "code": "NZ"},
    {"name": "Nicaragua", "code": "NI"},
    {"name": "Niger", "code": "NE"},
    {"name": "Nigeria", "code": "NG"},
    {"name": "Norway", "code": "NO"},
    {"name": "Oman", "code": "OM"},
    {"name": "Pakistan", "code": "PK"},
    {"name": "Palau", "code": "PW"},
    {"name": "Panama", "code": "PA"},
    {"name": "Papua New Guinea", "code": "PG"},
    {"name": "Paraguay", "code": "PY"},
    {"name": "Peru", "code": "PE"},
    {"name": "Philippines", "code": "PH"},
    {"name": "Poland", "code": "PL"},
    {"name": "Portugal", "code": "PT"},
    {"name": "Qatar", "code": "QA"},
    {"name": "Romania", "code": "RO"},
    {"name": "Russia", "code": "RU"},
    {"name": "Rwanda", "code": "RW"},
    {"name": "Saint Kitts and Nevis", "code": "KN"},
    {"name": "Saint Lucia", "code": "LC"},
    {"name": "Saint Vincent and the Grenadines", "code": "VC"},
    {"name": "Samoa", "code": "WS"},
    {"name": "San Marino", "code": "SM"},
    {"name": "Sao Tome and Principe", "code": "ST"},
    {"name": "Saudi Arabia", "code": "SA"},
    {"name": "Senegal", "code": "SN"},
    {"name": "Serbia", "code": "RS"},
    {"name": "Seychelles", "code": "SC"},
    {"name": "Sierra Leone", "code": "SL"},
    {"name": "Singapore", "code": "SG"},
    {"name": "Slovakia", "code": "SK"},
    {"name": "Slovenia", "code": "SI"},
    {"name": "Solomon Islands", "code": "SB"},
    {"name": "Somalia", "code": "SO"},
    {"name": "South Africa", "code": "ZA"},
    {"name": "South Sudan", "code": "SS"},
    {"name": "Spain", "code": "ES"},
    {"name": "Sri Lanka", "code": "LK"},
    {"name": "Sudan", "code": "SD"},
    {"name": "Suriname", "code": "SR"},
    {"name": "Sweden", "code": "SE"},
    {"name": "Switzerland", "code": "CH"},
    {"name": "Syria", "code": "SY"},
    {"name": "Taiwan", "code": "TW"},
    {"name": "Tajikistan", "code": "TJ"},
    {"name": "Tanzania", "code": "TZ"},
    {"name": "Thailand", "code": "TH"},
    {"name": "Togo", "code": "TG"},
    {"name": "Tonga", "code": "TO"},
    {"name": "Trinidad and Tobago", "code": "TT"},
    {"name": "Tunisia", "code": "TN"},
    {"name": "Turkey", "code": "TR"},
    {"name": "Turkmenistan", "code": "TM"},
    {"name": "Tuvalu", "code": "TV"},
    {"name": "Uganda", "code": "UG"},
    {"name": "Ukraine", "code": "UA"},
    {"name": "United Arab Emirates", "code": "AE"},
    {"name": "United Kingdom", "code": "GB"},
    {"name": "United States", "code": "US"},
    {"name": "Uruguay", "code": "UY"},
    {"name": "Uzbekistan", "code": "UZ"},
    {"name": "Vanuatu", "code": "VU"},
    {"name": "Vatican City", "code": "VA"},
    {"name": "Venezuela", "code": "VE"},
    {"name": "Vietnam", "code": "VN"},
    {"name": "Yemen", "code": "YE"},
    {"name": "Zambia", "code": "ZM"},
    {"name": "Zimbabwe", "code": "ZW"}
];

// Function to load countries (now using embedded data)
function loadCountries() {
    try {
        // Sort countries alphabetically by name
        const sortedCountries = [...countries].sort((a, b) => a.name.localeCompare(b.name));
        
        const countrySelect = document.getElementById('country');
        
        // Clear existing options except the first one
        while (countrySelect.children.length > 1) {
            countrySelect.removeChild(countrySelect.lastChild);
        }
        
        // Add countries to dropdown
        sortedCountries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${getFlagEmoji(country.code)} ${country.name}`;
            countrySelect.appendChild(option);
        });
        
        console.log(`Loaded ${sortedCountries.length} countries successfully`);
    } catch (error) {
        console.error('Error loading countries:', error);
        showError('Failed to load countries list. Please refresh the page.');
    }
}

// Search form event listener
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const product = document.getElementById('product').value.trim();
    const country = document.getElementById('country').value;
    
    if (!product || !country) {
        showError('Please enter both product name and select a country');
        return;
    }

    await searchPrices(product, country);
});

// Main search function
async function searchPrices(product, country) {
    const loadingDiv = document.getElementById('loadingDiv');
    const resultsDiv = document.getElementById('resultsDiv');
    const errorDiv = document.getElementById('errorDiv');
    const searchBtn = document.getElementById('searchBtn');

    // Show loading
    loadingDiv.classList.add('visible');
    resultsDiv.classList.remove('visible');
    resultsDiv.innerHTML = '';
    errorDiv.classList.remove('visible');
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Searching...</span>';

    try {
        const response = await fetch(`${API_BASE_URL}/compare-prices`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product: product,
                country: country,
                max_results: 10
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const results = await response.json();
        displayResults(results, product, country);

    } catch (error) {
        console.error('Error:', error);
        showError(`Failed to fetch prices: ${error.message}`);
        
        // Hide clear button on error
        const clearBtnContainer = document.getElementById('clearBtnContainer');
        const searchForm = document.getElementById('searchForm');
        clearBtnContainer.classList.remove('visible');
        searchForm.classList.remove('has-results');
    } finally {
        loadingDiv.classList.remove('visible');
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fas fa-search"></i><span>Search</span>';
    }
}

// Display search results
function displayResults(results, product, country) {
    const resultsDiv = document.getElementById('resultsDiv');
    const clearBtnContainer = document.getElementById('clearBtnContainer');
    const searchForm = document.getElementById('searchForm');
    
    if (!results || results.length === 0) {
        resultsDiv.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No results found</h3>
                <p>Try a different product name or country</p>
            </div>
        `;
        // Hide clear button for no results
        clearBtnContainer.classList.remove('visible');
        searchForm.classList.remove('has-results');
        return;
    }

    // Get country flag from the select option
    const countryOption = document.querySelector(`option[value="${country}"]`);
    const countryFlag = countryOption ? countryOption.textContent.split(' ')[0] : getFlagEmoji(country);
    
    // Update results header and show results section
    resultsDiv.innerHTML = `
        <div class="results-header">
            <h2 class="results-title">🎯 Found ${results.length} options for "${product}" in ${countryFlag}</h2>
            <p class="results-subtitle">Results sorted by price (lowest first)</p>
        </div>
        <div class="results-grid" id="resultsGrid"></div>
    `;
    
    // Show the results section
    resultsDiv.classList.add('visible');
    
    // Populate the results grid
    const resultsGrid = document.getElementById('resultsGrid');
    let gridHtml = '';

    if (results.length === 0) {
        gridHtml = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No results found</h3>
                <p>Try a different product name or country</p>
            </div>
        `;
    }
    
    results.forEach((item, index) => {
        const rankClass = index === 0 ? 'first' : index === 1 ? 'second' : index === 2 ? 'third' : '';
        const retailerName = extractRetailerName(item.link);
        
        gridHtml += `
            <div class="result-card">
                <div class="rank-badge ${rankClass}">${index + 1}</div>
                <div class="price-badge">
                    <span class="currency-flag">${getCurrencyFlag(item.currency)}</span>
                    ${item.price} ${item.currency}
                </div>
                <div class="product-name">${item.productName}</div>
                <a href="${item.link}" target="_blank" class="retailer-link">
                    <i class="fas fa-external-link-alt"></i>
                    View on ${retailerName}
                </a>
            </div>
        `;
    });
    
    resultsGrid.innerHTML = gridHtml;
    
    // Show clear button when results are displayed
    clearBtnContainer.classList.add('visible');
    searchForm.classList.add('has-results');
}

// Extract retailer name from URL
function extractRetailerName(url) {
    try {
        const domain = new URL(url).hostname.replace('www.', '');
        const retailerMap = {
            'amazon.com': 'Amazon US',
            'amazon.in': 'Amazon India',
            'amazon.co.uk': 'Amazon UK',
            'amazon.de': 'Amazon Germany',
            'amazon.fr': 'Amazon France',
            'amazon.co.jp': 'Amazon Japan',
            'bestbuy.com': 'Best Buy',
            'walmart.com': 'Walmart',
            'flipkart.com': 'Flipkart',
            'ebay.com': 'eBay',
            'target.com': 'Target',
            'newegg.com': 'Newegg'
        };
        return retailerMap[domain] || domain.split('.')[0].charAt(0).toUpperCase() + domain.split('.')[0].slice(1);
    } catch {
        return 'Retailer';
    }
}

// Get currency flag emoji
function getCurrencyFlag(currency) {
    const currencyFlags = {
        'USD': '💵', 'EUR': '💶', 'GBP': '💷', 'JPY': '💴',
        'INR': '🇮🇳', 'CAD': '🇨🇦', 'AUD': '🇦🇺', 'CHF': '🇨🇭',
        'SEK': '🇸🇪', 'NOK': '🇳🇴', 'DKK': '🇩🇰', 'PLN': '🇵🇱',
        'CZK': '🇨🇿', 'HUF': '🇭🇺', 'RUB': '🇷🇺', 'CNY': '🇨🇳',
        'KRW': '🇰🇷', 'SGD': '🇸🇬', 'MYR': '🇲🇾', 'THB': '🇹🇭',
        'PHP': '🇵🇭', 'IDR': '🇮🇩', 'VND': '🇻🇳', 'TWD': '🇹🇼',
        'HKD': '🇭🇰', 'NZD': '🇳🇿', 'ZAR': '🇿🇦', 'BRL': '🇧🇷',
        'MXN': '🇲🇽', 'ARS': '🇦🇷', 'CLP': '🇨🇱', 'COP': '🇨🇴',
        'PEN': '🇵🇪', 'TRY': '🇹🇷', 'AED': '🇦🇪', 'SAR': '🇸🇦',
        'QAR': '🇶🇦', 'KWD': '🇰🇼', 'BHD': '🇧🇭', 'OMR': '🇴🇲',
        'JOD': '🇯🇴', 'LBP': '🇱🇧', 'EGP': '🇪🇬', 'ILS': '🇮🇱'
    };
    return currencyFlags[currency] || '💰';
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('errorDiv');
    errorDiv.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> ${message}</div>`;
    errorDiv.classList.add('visible');
    
    // Hide results section when showing error
    const resultsDiv = document.getElementById('resultsDiv');
    resultsDiv.classList.remove('visible');
}

// Clear button functionality
document.getElementById('clearBtn').addEventListener('click', () => {
    const clearBtnContainer = document.getElementById('clearBtnContainer');
    const searchForm = document.getElementById('searchForm');
    
    document.getElementById('product').value = '';
    document.getElementById('country').value = '';
    document.getElementById('resultsDiv').innerHTML = '';
    document.getElementById('resultsDiv').classList.remove('visible');
    document.getElementById('errorDiv').classList.remove('visible');
    
    // Hide clear button after clearing
    clearBtnContainer.classList.remove('visible');
    searchForm.classList.remove('has-results');
    
    document.getElementById('product').focus();
});

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    loadCountries();
    document.getElementById('product').focus();
}); 