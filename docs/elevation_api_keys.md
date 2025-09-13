# Elevation Service API Keys

The elevation service supports multiple data providers, some of which require API keys for access.

## Required vs Optional API Keys

### 🟢 **No API Key Required** (Work Out of the Box)
- **USGS EPQS**: US government elevation data (high accuracy for US locations)
- **Open Topo Data**: Global SRTM/ASTER elevation datasets
- **OSM Elevation**: Community-driven elevation data

### 🟡 **API Key Recommended** (Enhanced Features)
- **Google Elevation API**: High-quality global coverage with consistent accuracy

## Setting Up Google Elevation API

### 1. Get a Google Cloud API Key
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Elevation API"
4. Go to "Credentials" and create an API key
5. Restrict the API key to "Elevation API" for security

### 2. Configure the API Key
Add your API key to your `.env` file:

```bash
GOOGLE_MAIN_API_KEY=your_google_api_key_here
```

### 3. Verify Setup
Test your configuration:

```bash
# Should now use all 4 providers including Google
uv run elevation-lookup lookup --lat 37.7749 --lon -122.4194
```

## Provider Selection Logic

The service automatically selects the best providers based on location:

**US Locations:**
- With Google API: USGS → Google → Open Topo Data → OSM
- Without Google API: USGS → Open Topo Data → OSM

**International Locations:**
- With Google API: Google → Open Topo Data → OSM
- Without Google API: Open Topo Data → OSM

**Ocean Areas:**
- With Google API: Google → Open Topo Data → OSM
- Without Google API: Open Topo Data → OSM

## Testing and CI

### Local Development
If you have a Google API key configured, all tests will run including Google provider tests.

### CI/GitHub Actions
The Google provider test is automatically skipped when no API key is available:

```
SKIPPED [1] tests/test_elevation.py:186: Google API key not available
```

This is intentional and ensures CI can run without requiring paid API keys.

## Cost Considerations

### Free Options
- **USGS**: Completely free, unlimited usage
- **Open Topo Data**: Free tier available, rate-limited
- **OSM Elevation**: Community service, rate-limited

### Paid Options
- **Google Elevation API**:
  - First 40,000 requests/month free
  - $5 per 1,000 requests after free tier
  - See [Google's pricing page](https://developers.google.com/maps/documentation/elevation/usage-and-billing)

## Recommendations

1. **For Development**: Use free providers (USGS + Open Topo Data + OSM)
2. **For Production with US focus**: Add Google API key for backup/validation
3. **For Production with Global focus**: Google API key highly recommended
4. **For High-Volume Applications**: Consider Google's enterprise pricing
