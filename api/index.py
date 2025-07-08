from openai import AzureOpenAI
import json
import os
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import asyncio
import aiohttp
from urllib.parse import quote_plus, urljoin, urlparse
import time
from fake_useragent import UserAgent
import cloudscraper
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_MODEL_NAME")

# Validate environment variables
if not all([AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT]):
    raise ValueError("Missing required Azure OpenAI environment variables")

# --- AZURE OPENAI CLIENT ---
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# --- FASTAPI SETUP ---
app = FastAPI(
    title="Dynamic Web Scraping Price Comparison Tool",
    description="Real-time price scraping from actual websites with AI analysis",
    version="2.0.0"
)

# Serve static files (JS, CSS)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../static")), name="static")

# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class PriceRequest(BaseModel):
    product: str
    country: str
    max_results: Optional[int] = 10

class PriceResponse(BaseModel):
    link: str
    price: str
    currency: str
    productName: str

# --- DYNAMIC WEB SCRAPING ENGINE ---

class DynamicPriceScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = cloudscraper.create_scraper()
        
        # Search engines to discover retailers dynamically
        self.search_engines = {
            'google': 'https://www.google.com/search?q={query}+buy+online+{country}&num=20',
            'bing': 'https://www.bing.com/search?q={query}+shopping+{country}',
            'duckduckgo': 'https://duckduckgo.com/html/?q={query}+buy+{country}'
        }
        
        # Known e-commerce patterns (will be expanded dynamically)
        self.ecommerce_patterns = {
            'amazon': {
                'url_pattern': r'amazon\.(com|co\.uk|de|fr|it|es|ca|in|com\.au|com\.br|jp|cn|com\.mx)',
                'search_path': '/s?k={}',
                'selectors': {
                    'container': ['[data-component-type="s-search-result"]', 'div[data-asin]', '.s-result-item'],
                    'title': ['h2 span', 'h2 a span', '.a-text-normal'],
                    'price': ['span.a-price-whole', 'span.a-price', '.a-price-range'],
                    'link': ['h2 a', '.a-link-normal', 'a[href*="/dp/"]']
                }
            },
            'ebay': {
                'url_pattern': r'ebay\.(com|co\.uk|de|fr|it|es|ca|in|com\.au)',
                'search_path': '/sch/i.html?_nkw={}',
                'selectors': {
                    'container': ['.s-item', '.sresult', 'li[data-view]'],
                    'title': ['.s-item__title', '.lvtitle', 'h3.s-item__title'],
                    'price': ['.s-item__price', '.lvprice', 'span.s-item__price'],
                    'link': ['.s-item__link', 'a.vip', 'a.s-item__link']
                }
            },
            'walmart': {
                'url_pattern': r'walmart\.(com|ca)',
                'search_path': '/search?q={}',
                'selectors': {
                    'container': ['[data-item-id]', 'div[data-tl-id]', '.search-result-gridview-item'],
                    'title': ['span[data-automation-id="product-title"]', '.product-title-link', 'a[class*="product-title"]'],
                    'price': ['[data-automation-id="product-price"]', '.price-current', 'span.price'],
                    'link': ['a[link-identifier]', 'a[href*="/ip/"]', '.product-title-link']
                }
            }
        }
        
        # Currency mapping
        self.currency_map = {
            'US': 'USD', 'UK': 'GBP', 'IN': 'INR', 'DE': 'EUR', 'FR': 'EUR',
            'CA': 'CAD', 'AU': 'AUD', 'JP': 'JPY', 'BR': 'BRL', 'MX': 'MXN',
            'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR', 'SE': 'SEK', 'CH': 'CHF'
        }

    def discover_retailers(self, product: str, country: str) -> List[str]:
        """Dynamically discover retailers selling the product in the country"""
        retailers = set()
        query = f"{product} buy online {country}"
        
        try:
            logger.info(f"Attempting to discover retailers via search for: {query}")
            
            # Search Google to find retailers
            search_url = self.search_engines['google'].format(query=quote_plus(query), country=country)
            headers = {
                'User-Agent': self.ua.random,
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=10)
            logger.info(f"Search response status: {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all links from search results
            link_count = 0
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                link_count += 1
                
                # Extract actual URL from Google's redirect
                if '/url?q=' in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'q' in parsed:
                        href = parsed['q'][0]
                
                # Check if it's an e-commerce site
                if self._is_ecommerce_url(href):
                    domain = self._extract_domain(href)
                    if domain:
                        retailers.add(domain)
            
            logger.info(f"Processed {link_count} links, found {len(retailers)} e-commerce retailers")
            
            if len(retailers) > 0:
                logger.info(f"Discovered retailers: {list(retailers)}")
                return list(retailers)[:10]  # Limit to top 10
            else:
                logger.warning(f"No retailers discovered via search, falling back to known retailers for {country}")
                return self._get_fallback_retailers(country)
            
        except Exception as e:
            logger.error(f"Error discovering retailers: {e}")
            logger.info(f"Falling back to known retailers for {country}")
            # Fallback to known retailers for the country
            return self._get_fallback_retailers(country)

    def _is_ecommerce_url(self, url: str) -> bool:
        """Check if URL is likely an e-commerce site"""
        ecommerce_indicators = [
            'shop', 'store', 'buy', 'product', 'item', '/dp/', '/p/', 
            'add-to-cart', 'checkout', 'price', 'sale', 'deals',
            'amazon', 'ebay', 'walmart', 'target', 'bestbuy', 'flipkart',
            'alibaba', 'etsy', 'newegg', 'costco', 'homedepot'
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in ecommerce_indicators)

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract clean domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain if domain else None
        except:
            return None

    def _get_fallback_retailers(self, country: str) -> List[str]:
        """Get fallback retailers if discovery fails"""
        fallback_map = {
            'US': ['amazon.com', 'walmart.com', 'target.com', 'ebay.com', 'bestbuy.com'],
            'UK': ['amazon.co.uk', 'ebay.co.uk', 'argos.co.uk', 'currys.co.uk'],
            'IN': ['amazon.in', 'flipkart.com', 'snapdeal.com', 'myntra.com'],
            'DE': ['amazon.de', 'ebay.de', 'otto.de', 'mediamarkt.de'],
            'FR': ['amazon.fr', 'cdiscount.com', 'fnac.com', 'ebay.fr'],
            'CA': ['amazon.ca', 'walmart.ca', 'bestbuy.ca', 'ebay.ca'],
            'AU': ['amazon.com.au', 'ebay.com.au', 'jbhifi.com.au', 'kogan.com']
        }
        
        country_upper = country.upper()
        retailers = fallback_map.get(country_upper, ['amazon.com', 'ebay.com'])
        
        logger.info(f"Getting fallback retailers for country '{country}' (normalized: '{country_upper}')")
        logger.info(f"Fallback retailers: {retailers}")
        
        return retailers

    def scrape_retailer(self, retailer_domain: str, product: str) -> List[Dict]:
        """Scrape product data from a specific retailer"""
        results = []
        
        try:
            # Determine retailer type and get scraping config
            retailer_config = self._get_retailer_config(retailer_domain)
            
            # Build search URL
            if retailer_config:
                search_url = f"https://{retailer_domain}{retailer_config['search_path'].format(quote_plus(product))}"
            else:
                # Generic search URL pattern
                search_url = f"https://{retailer_domain}/search?q={quote_plus(product)}"
            
            logger.info(f"Scraping {search_url}")
            
            # Make request
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract products
            if retailer_config:
                products = self._extract_products_with_config(soup, retailer_config, retailer_domain)
            else:
                products = self._extract_products_generic(soup, retailer_domain, product)
            
            results.extend(products[:5])  # Limit to 5 products per retailer
            
        except Exception as e:
            logger.error(f"Error scraping {retailer_domain}: {e}")
        
        return results

    def _get_retailer_config(self, domain: str) -> Optional[Dict]:
        """Get scraping configuration for known retailers"""
        for retailer_type, config in self.ecommerce_patterns.items():
            if re.search(config['url_pattern'], domain):
                return config
        return None

    def _extract_products_with_config(self, soup: BeautifulSoup, config: Dict, domain: str) -> List[Dict]:
        """Extract products using known selectors"""
        products = []
        
        # Try each container selector
        containers = []
        for selector in config['selectors']['container']:
            containers.extend(soup.select(selector))
        
        for container in containers[:10]:  # Process up to 10 items
            try:
                # Extract title
                title = None
                for title_selector in config['selectors']['title']:
                    title_elem = container.select_one(title_selector)
                    if title_elem:
                        title = title_elem.text.strip()
                        break
                
                # Extract price
                price = None
                for price_selector in config['selectors']['price']:
                    price_elem = container.select_one(price_selector)
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Extract numeric price
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                        if price_match:
                            price = price_match.group()
                            break
                
                # Extract link
                link = None
                for link_selector in config['selectors']['link']:
                    link_elem = container.select_one(link_selector)
                    if link_elem and link_elem.get('href'):
                        link = urljoin(f"https://{domain}", link_elem['href'])
                        break
                
                if title and price and link:
                    products.append({
                        'productName': title,
                        'price': price,
                        'link': link,
                        'retailer': domain
                    })
                    
            except Exception as e:
                logger.debug(f"Error extracting product: {e}")
                continue
        
        return products

    def _extract_products_generic(self, soup: BeautifulSoup, domain: str, search_query: str) -> List[Dict]:
        """Generic extraction for unknown retailers"""
        products = []
        
        # Common patterns for product listings
        possible_containers = [
            soup.find_all('div', class_=re.compile(r'product|item|result|card|listing', re.I)),
            soup.find_all('li', class_=re.compile(r'product|item|result', re.I)),
            soup.find_all('article', class_=re.compile(r'product|item', re.I))
        ]
        
        for containers in possible_containers:
            for container in containers[:10]:
                try:
                    # Look for title
                    title_elem = (
                        container.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|name|heading', re.I)) or
                        container.find('a', class_=re.compile(r'title|name|product', re.I)) or
                        container.find('span', class_=re.compile(r'title|name', re.I))
                    )
                    
                    # Look for price
                    price_elem = (
                        container.find(['span', 'div'], class_=re.compile(r'price|cost|amount', re.I)) or
                        container.find(text=re.compile(r'[\$£€₹]\s*[\d,]+\.?\d*'))
                    )
                    
                    # Look for link
                    link_elem = container.find('a', href=True)
                    
                    if title_elem and price_elem:
                        title = title_elem.text.strip() if hasattr(title_elem, 'text') else str(title_elem).strip()
                        
                        # Extract price
                        price_text = price_elem.text if hasattr(price_elem, 'text') else str(price_elem)
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                        
                        if price_match and link_elem:
                            products.append({
                                'productName': title,
                                'price': price_match.group(),
                                'link': urljoin(f"https://{domain}", link_elem['href']),
                                'retailer': domain
                            })
                            
                except Exception as e:
                    continue
        
        # If no products found, try finding any links with the search query
        if not products:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.text.strip()
                
                if search_query.lower() in text.lower() and '/product' in href or '/item' in href:
                    # Try to find price nearby
                    parent = link.parent
                    price_match = re.search(r'[\$£€₹]\s*([\d,]+\.?\d*)', parent.text if parent else '')
                    
                    if price_match:
                        products.append({
                            'productName': text,
                            'price': price_match.group(1).replace(',', ''),
                            'link': urljoin(f"https://{domain}", href),
                            'retailer': domain
                        })
        
        return products

    def get_currency_for_country(self, country: str) -> str:
        """Get currency for country"""
        return self.currency_map.get(country.upper(), 'USD')

    async def scrape_all_retailers_async(self, product: str, country: str) -> List[Dict]:
        """Asynchronously scrape all discovered retailers"""
        logger.info(f"Starting scrape_all_retailers_async for '{product}' in '{country}'")
        
        # First, discover retailers
        retailers = self.discover_retailers(product, country)
        logger.info(f"Discovery returned {len(retailers)} retailers: {retailers}")
        
        if not retailers:
            logger.warning(f"No retailers found for {product} in {country}")
            # Force use fallback retailers for debugging
            logger.info("Forcing fallback retailers for debugging...")
            retailers = self._get_fallback_retailers(country)
            logger.info(f"Using fallback retailers: {retailers}")
        
        if not retailers:
            logger.error("Even fallback retailers are empty!")
            return []
        
        # Scrape all retailers in parallel
        all_results = []
        logger.info(f"Starting parallel scraping of {len(retailers)} retailers")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_retailer = {
                executor.submit(self.scrape_retailer, retailer, product): retailer 
                for retailer in retailers
            }
            
            for future in as_completed(future_to_retailer):
                retailer = future_to_retailer[future]
                try:
                    results = future.result()
                    logger.info(f"Retailer {retailer} returned {len(results)} results")
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error scraping {retailer}: {e}")
        
        logger.info(f"Total scraped results: {len(all_results)}")
        return all_results

# --- AI ANALYSIS ---

def analyze_scraped_data_with_ai(scraped_data: List[Dict], product_query: str, country: str, currency: str) -> List[Dict]:
    """Use AI to clean, standardize, and enrich the scraped data"""
    
    if not scraped_data:
        return []
    
    # Pre-filter: Remove obviously irrelevant products before AI processing
    filtered_data = []
    for item in scraped_data:
        product_name = item.get('productName', '').lower()
        query_lower = product_query.lower()
        
        # For iPhone searches, only keep Apple/iPhone products
        if 'iphone' in query_lower:
            if 'iphone' in product_name or 'apple' in product_name:
                filtered_data.append(item)
            else:
                logger.info(f"Pre-filtering out non-iPhone product: {item.get('productName', 'Unknown')}")
        # For specific brand searches, filter by brand
        elif any(brand in query_lower for brand in ['samsung', 'motorola', 'google', 'oneplus']):
            brand_found = False
            for brand in ['samsung', 'motorola', 'google', 'oneplus']:
                if brand in query_lower and brand in product_name:
                    brand_found = True
                    break
            if brand_found:
                filtered_data.append(item)
            else:
                logger.info(f"Pre-filtering out non-{query_lower} product: {item.get('productName', 'Unknown')}")
        else:
            # For generic searches, keep all products
            filtered_data.append(item)
    
    logger.info(f"Pre-filtering: {len(scraped_data)} -> {len(filtered_data)} products")
    
    if not filtered_data:
        return []
    
    prompt = f"""
You are analyzing real scraped e-commerce data for "{product_query}" in {country}.

**CRITICAL FILTERING RULES:**
- If searching for "iphone" or "iPhone": ONLY return Apple iPhone products, NEVER Samsung/Motorola/other brands
- If searching for "samsung": ONLY return Samsung products
- If searching for "motorola": ONLY return Motorola products
- REJECT any product that doesn't match the exact brand/model being searched

**Raw Scraped Data:**
{json.dumps(filtered_data, indent=2)}

**Your Tasks:**
1. **STRICT RELEVANCE FILTERING**: 
   - For iPhone searches: ONLY Apple iPhone products allowed
   - Remove ALL Samsung, Motorola, Google, OnePlus, or any non-Apple products
   - Product name must contain the actual model being searched (e.g., "iPhone 15" for iPhone 15 searches)

2. **Clean and Standardize Product Names**: 
   - Remove unnecessary details (shipping info, seller names, promotional text)
   - Standardize the product name across all entries
   - Keep important variants (size, color, model, carrier) if relevant

3. **Validate and Fix Prices**:
   - Ensure all prices are valid numbers (remove any non-numeric characters)
   - Remove any that seem incorrect (too high/low for the product type)
   - Convert all to {currency} if needed

4. **Quality Control**:
   - Remove duplicate listings (same product, same price, same retailer)
   - Flag any deals or special offers in the product name

5. **Sort by Price**: Arrange from lowest to highest

**Output Format (JSON)**:
{{
    "results": [
        {{
            "link": "exact_url_from_scraped_data",
            "price": "numeric_price_only",
            "currency": "{currency}",
            "productName": "standardized_product_name"
        }}
    ]
}}

Return ONLY products that exactly match the search query. Do not invent new URLs or data.
REJECT ALL products that are not the exact brand/model being searched for.
"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a data cleaning expert. You analyze and standardize scraped e-commerce data."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('results', [])
        
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        # Return cleaned scraped data as fallback
        return [{
            'link': item['link'],
            'price': item['price'],
            'currency': currency,
            'productName': item['productName']
        } for item in scraped_data if all(key in item for key in ['link', 'price', 'productName'])]

# --- MAIN PRICE COMPARISON FUNCTION ---

async def get_product_prices_dynamic(product_query: str, country_code: str, max_results: int = 10) -> List[Dict]:
    """
    Main function that coordinates web scraping and AI analysis
    """
    scraper = DynamicPriceScraper()
    currency = scraper.get_currency_for_country(country_code)
    
    logger.info(f"Starting web scraping for '{product_query}' in {country_code}")
    logger.info(f"Currency for {country_code}: {currency}")
    
    # Test fallback retailers first for debugging
    fallback_retailers = scraper._get_fallback_retailers(country_code)
    logger.info(f"Available fallback retailers for {country_code}: {fallback_retailers}")
    
    # Step 1: Scrape real data from discovered retailers
    scraped_data = await scraper.scrape_all_retailers_async(product_query, country_code)
    logger.info(f"scraped_data: {scraped_data}")
    
    if not scraped_data:
        logger.warning("No data scraped, returning empty results")
        return []
    
    logger.info(f"Scraped {len(scraped_data)} products")
    
    # Step 2: Use AI to clean and standardize the data
    cleaned_data = analyze_scraped_data_with_ai(scraped_data, product_query, country_code, currency)
    
    # Step 3: Return top results
    return cleaned_data[:max_results]

# --- API ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Dynamic Web Scraping Price Comparison Tool is running"}

@app.post("/compare-prices", response_model=List[PriceResponse])
async def compare_prices(request: PriceRequest):
    """
    Compare prices by actually scraping the web in real-time.
    
    This endpoint:
    1. Discovers retailers selling the product in the specified country
    2. Scrapes actual product listings from those retailers
    3. Uses AI to clean and standardize the data
    4. Returns sorted results
    """
    try:
        if not request.product.strip():
            raise HTTPException(status_code=400, detail="Product name cannot be empty")
        
        if not request.country.strip():
            raise HTTPException(status_code=400, detail="Country code cannot be empty")
        
        # Get real scraped data
        results = await get_product_prices_dynamic(
            request.product, 
            request.country, 
            request.max_results
        )
        
        if not results:
            raise HTTPException(
                status_code=404, 
                detail=f"No products found for '{request.product}' in {request.country}. This could be due to rate limiting or the product not being available."
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# --- DIRECT USAGE FUNCTION ---

async def fetch_product_prices(product: str, country: str, max_results: int = 10) -> List[Dict]:
    """
    Direct function for fetching prices without FastAPI
    """
    return await get_product_prices_dynamic(product, country, max_results)

# --- MAIN ---
if __name__ == "__main__":
    print("🚀 Starting Dynamic Web Scraping Price Comparison API...")
    print("🌐 This version actually scrapes the web in real-time!")
    print(f"📍 Server: http://0.0.0.0:8000")
    print(f"📚 Documentation: http://0.0.0.0:8000/docs")
    print(f"🔍 Endpoint: POST /compare-prices")
    uvicorn.run(app, host="0.0.0.0", port=8000)