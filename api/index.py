from openai import AzureOpenAI
import json
import os
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup
import cloudscraper
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from fake_useragent import UserAgent
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import logging

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_MODEL_NAME")

if not all([AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT]):
    raise ValueError("Missing required Azure OpenAI environment variables")

# Azure OpenAI Client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# FastAPI Setup
app = FastAPI(
    title="Dynamic Web Scraping Price Comparison Tool",
    description="Real-time price scraping from actual websites with AI analysis",
    version="2.0.0"
)

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class PriceRequest(BaseModel):
    product: str
    country: str
    max_results: Optional[int] = 10

class PriceResponse(BaseModel):
    link: str
    price: str
    currency: str
    productName: str

# Dynamic Web Scraping Engine
class DynamicPriceScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = cloudscraper.create_scraper()
        
        self.search_engines = {
            'google': 'https://www.google.com/search?q={query}+buy+online+{country}&num=20',
            'bing': 'https://www.bing.com/search?q={query}+shopping+{country}',
            'duckduckgo': 'https://duckduckgo.com/html/?q={query}+buy+{country}'
        }
        
        self.currency_map = {
            'US': 'USD', 'UK': 'GBP', 'IN': 'INR', 'DE': 'EUR', 'FR': 'EUR',
            'CA': 'CAD', 'AU': 'AUD', 'JP': 'JPY', 'BR': 'BRL', 'MX': 'MXN',
            'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR', 'SE': 'SEK', 'CH': 'CHF'
        }

    def discover_retailers(self, product: str, country: str) -> List[str]:
        """Dynamically discover retailers selling the product in the country"""
        retailers = set()
        
        # Multiple search strategies for better diversity
        search_strategies = [
            f"{product} buy online {country}",
            f"{product} shopping {country}",
            f"{product} price comparison {country}",
            f"where to buy {product} {country}",
            f"{product} online store {country}",
            f"best {product} deals {country}"
        ]
        
        # Use multiple search engines for diversity
        search_engines = ['google', 'bing', 'duckduckgo']
        
        for strategy in search_strategies[:3]:  # Use top 3 strategies
            for engine in search_engines[:2]:  # Use 2 search engines
                try:
                    if engine == 'google':
                        search_url = f"https://www.google.com/search?q={quote_plus(strategy)}&num=20"
                    elif engine == 'bing':
                        search_url = f"https://www.bing.com/search?q={quote_plus(strategy)}"
                    else:
                        search_url = f"https://duckduckgo.com/html/?q={quote_plus(strategy)}"
                    
                    headers = {
                        'User-Agent': self.ua.random,
                        'Accept-Language': self._get_country_language(country),
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    response = self.session.get(search_url, headers=headers, timeout=8)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        
                        # Extract actual URL from search engine redirects
                        if '/url?q=' in href:
                            parsed = parse_qs(urlparse(href).query)
                            if 'q' in parsed:
                                href = parsed['q'][0]
                        elif href.startswith('/search') or href.startswith('http://www.bing.com'):
                            continue
                        
                        if self._is_ecommerce_url(href, country):
                            domain = self._extract_domain(href)
                            if domain and self._is_valid_retailer(domain, country):
                                retailers.add(domain)
                    
                    if len(retailers) >= 15:  # Stop if we have enough diversity
                        break
                        
                except Exception as e:
                    logger.debug(f"Error with {engine} search: {e}")
                    continue
            
            if len(retailers) >= 15:
                break
        
        # Prioritize local retailers over global ones
        prioritized_retailers = self._prioritize_local_retailers(list(retailers), country)
        
        if prioritized_retailers:
            logger.info(f"Discovered {len(prioritized_retailers)} retailers for {product} in {country}")
            return prioritized_retailers[:10]
        else:
            logger.warning(f"No retailers discovered for {product} in {country}")
            return []

    def _get_country_language(self, country: str) -> str:
        """Get appropriate language header for country"""
        language_map = {
            'US': 'en-US,en;q=0.9',
            'UK': 'en-GB,en;q=0.9',
            'IN': 'en-IN,hi;q=0.8,en;q=0.7',
            'DE': 'de-DE,de;q=0.9,en;q=0.7',
            'FR': 'fr-FR,fr;q=0.9,en;q=0.7',
            'CA': 'en-CA,fr-CA;q=0.8,en;q=0.7',
            'AU': 'en-AU,en;q=0.9',
            'JP': 'ja-JP,ja;q=0.9,en;q=0.7',
            'BR': 'pt-BR,pt;q=0.9,en;q=0.7'
        }
        return language_map.get(country.upper(), 'en-US,en;q=0.9')

    def _is_ecommerce_url(self, url: str, country: str) -> bool:
        """Check if URL is likely an e-commerce site with country-specific indicators"""
        if not url or 'javascript:' in url or 'mailto:' in url:
            return False
        
        # Global e-commerce indicators
        global_indicators = [
            'shop', 'store', 'buy', 'product', 'item', '/dp/', '/p/', 
            'add-to-cart', 'checkout', 'price', 'sale', 'deals', 'cart',
            'purchase', 'order', 'catalog', 'marketplace'
        ]
        
        # Country-specific e-commerce sites
        country_specific = {
            'IN': ['flipkart', 'myntra', 'snapdeal', 'paytmmall', 'tatacliq', 'shopclues', 
                   'bigbasket', 'grofers', 'nykaa', 'ajio', 'reliance', 'croma'],
            'DE': ['otto', 'zalando', 'mediamarkt', 'saturn', 'alternate', 'idealo'],
            'FR': ['cdiscount', 'fnac', 'darty', 'boulanger', 'rueducommerce'],
            'UK': ['argos', 'currys', 'johnlewis', 'tesco', 'asda', 'very'],
            'CA': ['canadiantire', 'bestbuy.ca', 'costco.ca', 'walmart.ca'],
            'AU': ['jbhifi', 'kogan', 'catch', 'bigw', 'dicksmith'],
            'JP': ['rakuten', 'yahoo', 'yodobashi', 'bic-camera'],
            'BR': ['mercadolivre', 'americanas', 'submarino', 'casasbahia']
        }
        
        url_lower = url.lower()
        
        # Check country-specific sites first (higher priority)
        country_sites = country_specific.get(country.upper(), [])
        if any(site in url_lower for site in country_sites):
            return True
        
        # Check global indicators
        return any(indicator in url_lower for indicator in global_indicators)

    def _is_valid_retailer(self, domain: str, country: str) -> bool:
        """Filter out non-retail domains"""
        blacklist = [
            'google', 'bing', 'yahoo', 'facebook', 'twitter', 'instagram',
            'youtube', 'wikipedia', 'reddit', 'pinterest', 'linkedin',
            'search', 'maps', 'news', 'blog', 'forum', 'review'
        ]
        
        if any(blocked in domain.lower() for blocked in blacklist):
            return False
        
        # Must have valid TLD
        if '.' not in domain or len(domain.split('.')) < 2:
            return False
        
        return True

    def _prioritize_local_retailers(self, retailers: List[str], country: str) -> List[str]:
        """Prioritize local/regional retailers over global ones"""
        local_retailers = []
        regional_retailers = []
        global_retailers = []
        
        # Country-specific domains
        country_domains = {
            'IN': ['.in'],
            'UK': ['.co.uk', '.uk'],
            'DE': ['.de'],
            'FR': ['.fr'],
            'CA': ['.ca'],
            'AU': ['.com.au', '.au'],
            'JP': ['.jp', '.co.jp'],
            'BR': ['.com.br', '.br']
        }
        
        # Major global retailers (lower priority)
        global_brands = ['amazon', 'ebay', 'walmart', 'alibaba']
        
        for retailer in retailers:
            retailer_lower = retailer.lower()
            
            # Check if it's a local domain
            country_tlds = country_domains.get(country.upper(), [])
            if any(tld in retailer_lower for tld in country_tlds):
                local_retailers.append(retailer)
            # Check if it's a global brand
            elif any(brand in retailer_lower for brand in global_brands):
                global_retailers.append(retailer)
            else:
                regional_retailers.append(retailer)
        
        # Return prioritized list: local first, then regional, then global (limited)
        return local_retailers + regional_retailers + global_retailers[:2]

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract clean domain from URL"""
        try:
            domain = urlparse(url).netloc.lower()
            return domain[4:] if domain.startswith('www.') else domain
        except Exception:
            return None

    def scrape_retailer(self, retailer_domain: str, product: str) -> List[Dict]:
        """Scrape product data from a specific retailer"""
        try:
            # No specific retailer patterns, rely on generic extraction
            search_url = f"https://{retailer_domain}/search?q={quote_plus(product)}"
            
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
            
            products = self._extract_products_generic(soup, retailer_domain, product)
            
            return products[:5]  # Limit to 5 products per retailer
            
        except Exception as e:
            logger.error(f"Error scraping {retailer_domain}: {e}")
            return []

    def _extract_products_generic(self, soup: BeautifulSoup, domain: str, search_query: str) -> List[Dict]:
        """Generic extraction for unknown retailers"""
        products = []
        
        possible_containers = [
            soup.find_all('div', class_=re.compile(r'product|item|result|card|listing', re.I)),
            soup.find_all('li', class_=re.compile(r'product|item|result', re.I)),
            soup.find_all('article', class_=re.compile(r'product|item', re.I))
        ]
        
        for containers in possible_containers:
            for container in containers[:10]:
                try:
                    title_elem = (
                        container.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|name|heading', re.I)) or
                        container.find('a', class_=re.compile(r'title|name|product', re.I)) or
                        container.find('span', class_=re.compile(r'title|name', re.I))
                    )
                    
                    price_elem = (
                        container.find(['span', 'div'], class_=re.compile(r'price|cost|amount', re.I)) or
                        container.find(text=re.compile(r'[\$£€₹]\s*[\d,]+\.?\d*'))
                    )
                    
                    link_elem = container.find('a', href=True)
                    
                    if title_elem and price_elem and link_elem:
                        title = title_elem.text.strip() if hasattr(title_elem, 'text') else str(title_elem).strip()
                        price_text = price_elem.text if hasattr(price_elem, 'text') else str(price_elem)
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                        
                        if price_match:
                            products.append({
                                'productName': title,
                                'price': price_match.group(),
                                'link': urljoin(f"https://{domain}", link_elem['href']),
                                'retailer': domain
                            })
                except Exception:
                    continue
        
        return products

    def get_currency_for_country(self, country: str) -> str:
        """Get currency for country"""
        return self.currency_map.get(country.upper(), 'USD')

    async def scrape_all_retailers_async(self, product: str, country: str) -> List[Dict]:
        """Asynchronously scrape all discovered retailers"""
        retailers = self.discover_retailers(product, country)
        
        if not retailers:
            return []
        
        all_results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_retailer = {
                executor.submit(self.scrape_retailer, retailer, product): retailer 
                for retailer in retailers
            }
            
            for future in as_completed(future_to_retailer):
                retailer = future_to_retailer[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Error scraping {retailer}: {e}")
        
        return all_results

# AI Analysis
def analyze_scraped_data_with_ai(scraped_data: List[Dict], product_query: str, country: str, currency: str) -> List[Dict]:
    """Use AI to clean, standardize, and enrich the scraped data"""
    if not scraped_data:
        return []
    
    # Pre-filter data by brand relevance
    filtered_data = []
    query_lower = product_query.lower()
    
    for item in scraped_data:
        product_name = item.get('productName', '').lower()
        
        if 'iphone' in query_lower:
            if 'iphone' in product_name or 'apple' in product_name:
                filtered_data.append(item)
        elif any(brand in query_lower for brand in ['samsung', 'motorola', 'google', 'oneplus']):
            brand_found = any(brand in query_lower and brand in product_name 
                            for brand in ['samsung', 'motorola', 'google', 'oneplus'])
            if brand_found:
                filtered_data.append(item)
        else:
            filtered_data.append(item)
    
    if not filtered_data:
        return []
    
    prompt = f"""
        Analyze and clean this e-commerce data for "{product_query}" in {country}.

        Data: {json.dumps(filtered_data, indent=2)}

        Tasks:
        1. Filter for exact brand/model matches only
        2. Standardize product names (remove shipping/seller info)
        3. Validate prices (numeric only, reasonable for product type)
        4. Remove duplicates
        5. Sort by price (lowest first)

        Return JSON format:
        {{
            "results": [
                {{
                    "link": "exact_url_from_data",
                    "price": "numeric_price_only",
                    "currency": "{currency}",
                    "productName": "standardized_name"
                }}
            ]
        }}

        Only return products matching the exact search query.
    """

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a data cleaning expert for e-commerce data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('results', [])
        
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return [{
            'link': item['link'],
            'price': item['price'],
            'currency': currency,
            'productName': item['productName']
        } for item in filtered_data if all(key in item for key in ['link', 'price', 'productName'])]

# Main Function
async def get_product_prices_dynamic(product_query: str, country_code: str, max_results: int = 10) -> List[Dict]:
    """Main function that coordinates web scraping and AI analysis"""
    scraper = DynamicPriceScraper()
    currency = scraper.get_currency_for_country(country_code)
    
    scraped_data = await scraper.scrape_all_retailers_async(product_query, country_code)
    
    if not scraped_data:
        return []
    
    cleaned_data = analyze_scraped_data_with_ai(scraped_data, product_query, country_code, currency)
    return cleaned_data[:max_results]

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Dynamic Web Scraping Price Comparison Tool is running"}

@app.post("/compare-prices", response_model=List[PriceResponse])
async def compare_prices(request: PriceRequest):
    """Compare prices by scraping the web in real-time"""
    try:
        if not request.product.strip():
            raise HTTPException(status_code=400, detail="Product name cannot be empty")
        
        if not request.country.strip():
            raise HTTPException(status_code=400, detail="Country code cannot be empty")
        
        results = await get_product_prices_dynamic(
            request.product, 
            request.country, 
            request.max_results
        )
        
        if not results:
            raise HTTPException(
                status_code=404, 
                detail=f"No products found for '{request.product}' in {request.country}"
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Main
if __name__ == "__main__":
    print("🚀 Starting Dynamic Web Scraping Price Comparison API...")
    print("🌐 Real-time web scraping enabled!")
    print("📍 Server: http://0.0.0.0:8000")
    print("📚 Documentation: http://0.0.0.0:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)