# Universal Dynamic Price Comparison API

A **fully dynamic** price comparison tool that automatically discovers retailers and compares prices for **ANY product** in **ANY country** without static mappings. Built with FastAPI and Azure OpenAI.

## 🌟 Key Features

🚀 **Fully Dynamic**: No hardcoded retailer lists - AI discovers relevant stores automatically  
🌍 **Universal Coverage**: Works for ANY product in ANY country  
🔍 **Smart Discovery**: Automatically identifies local retailers, marketplaces, and specialty stores  
🎯 **Single Endpoint**: Clean, simple API with one endpoint for all price comparisons  
⚡ **FastAPI Powered**: High-performance async API with automatic documentation  
📊 **Exact JSON Format**: Returns data in your specified format, sorted by price  

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd bharatX

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_CHAT_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_CHAT_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
```

**How to get these values:**
1. Go to **Azure Portal** → **Azure OpenAI Service**
2. **Keys and Endpoint** → Copy your API key and endpoint
3. **Model deployments** → Note your deployment name

### 3. Start API Server

```bash
# Start FastAPI server
python main.py
```

### 4. Access API

- **API Server**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📋 API Endpoint

### 🔍 Compare Prices
**POST** `/compare-prices`

**Single endpoint** that dynamically discovers and compares prices across multiple retailers for ANY product in ANY country.

```bash
curl -X POST "http://localhost:8000/compare-prices" \
     -H "Content-Type: application/json" \
     -d '{
       "product": "iPhone 15 Pro 256GB",
       "country": "US",
       "max_results": 5
     }'
```

**Input Parameters:**
- `product` (string): Product name to search for
- `country` (string): ISO country code (US, UK, IN, DE, JP, etc.)
- `max_results` (int, optional): Maximum results to return (default: 10)

**Response Format:**
```json
[
    {
        "link": "https://dynamically-discovered-retailer.com/product",
        "price": "999",
        "currency": "USD",
        "productName": "Apple iPhone 15 Pro 256GB"
    },
    {
        "link": "https://another-retailer.com/product", 
        "price": "1099",
        "currency": "USD",
        "productName": "Apple iPhone 15 Pro 256GB"
    }
]
```

**Features:**
- ✅ Results automatically sorted by price (lowest first)
- ✅ Dynamically discovers relevant retailers for each country
- ✅ Includes local marketplaces and international stores
- ✅ Appropriate currency for each country
- ✅ Clean, simple 4-field response format

## 🔧 Dynamic Discovery Examples

The tool automatically discovers relevant retailers based on country and product category:

### 🇺🇸 Electronics in US
**Discovered**: Amazon, Best Buy, Walmart, Newegg, B&H Photo, eBay

### 🇯🇵 Electronics in Japan  
**Discovered**: Amazon.co.jp, Yodobashi Camera, Bic Camera, Rakuten

### 🇩🇪 Fashion in Germany
**Discovered**: Amazon.de, Zalando, Otto, About You, local stores

### 🇮🇳 Home Goods in India
**Discovered**: Amazon.in, Flipkart, Pepperfry, Urban Ladder

### 🇬🇧 Books in UK
**Discovered**: Amazon.co.uk, Waterstones, WHSmith, Foyles

## 💻 Integration Examples

### Python Client
```python
import requests

def compare_prices(product, country, max_results=5):
    response = requests.post(
        "http://localhost:8000/compare-prices",
        json={
            "product": product,
            "country": country,
            "max_results": max_results
        }
    )
    return response.json()

# Example usage
results = compare_prices("Samsung Galaxy S24", "DE")
print(f"Found {len(results)} options:")
for item in results:
    print(f"{item['retailer']}: {item['price']} {item['currency']}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function comparePrices(product, country, maxResults = 5) {
    try {
        const response = await axios.post('http://localhost:8000/compare-prices', {
            product,
            country, 
            max_results: maxResults
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        return [];
    }
}

// Example usage
comparePrices('Nintendo Switch OLED', 'JP')
    .then(results => {
        console.log(`Found ${results.length} options:`);
        results.forEach(item => {
            console.log(`${item.retailer}: ${item.price} ${item.currency}`);
        });
    });
```

### cURL Examples
```bash
# Search for laptop in US
curl -X POST "http://localhost:8000/compare-prices" \
     -H "Content-Type: application/json" \
     -d '{"product": "MacBook Air M3", "country": "US", "max_results": 3}'

# Search for sneakers in Germany
curl -X POST "http://localhost:8000/compare-prices" \
     -H "Content-Type: application/json" \
     -d '{"product": "Nike Air Force 1", "country": "DE"}'

# Search for smartphone in India
curl -X POST "http://localhost:8000/compare-prices" \
     -H "Content-Type: application/json" \
     -d '{"product": "iPhone 15", "country": "IN"}'
```

## 🔍 Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
    "status": "healthy",
    "message": "Universal Price Comparison Tool is running"
}
``` 