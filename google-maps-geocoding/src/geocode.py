from googlemaps import Client as GoogleMaps

def geocode_address(address):
    # Initialize the Google Maps client with your API key
    gmaps = GoogleMaps(api_key='YOUR_API_KEY')

    # Geocode the address
    geocode_result = gmaps.geocode(address)

    if geocode_result:
        # Extract latitude and longitude
        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']
        return latitude, longitude
    else:
        return None, None

# Example usage
if __name__ == "__main__":
    address = "1600 Amphitheatre Parkway, Mountain View, CA"
    lat, lng = geocode_address(address)
    print(f"Latitude: {lat}, Longitude: {lng}")