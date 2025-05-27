# Google Maps Geocoding Project

This project provides functionality to geocode addresses using the Google Maps API. It includes a Python script that takes an address as input and returns the corresponding latitude and longitude.

## Project Structure

```
google-maps-geocoding
├── src
│   ├── geocode.py
│   └── utils
│       └── __init__.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd google-maps-geocoding
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Obtain a Google Maps API key:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project and enable the Google Maps Geocoding API.
   - Generate an API key and restrict it as necessary.

4. Set your API key in the environment variable:
   ```
   export GOOGLE_MAPS_API_KEY='your_api_key_here'
   ```

## Usage

To geocode an address, you can use the `geocode_address` function from the `geocode.py` script. Here is an example:

```python
from src.geocode import geocode_address

address = "1600 Amphitheatre Parkway, Mountain View, CA"
latitude, longitude = geocode_address(address)
print(f"Latitude: {latitude}, Longitude: {longitude}")
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.