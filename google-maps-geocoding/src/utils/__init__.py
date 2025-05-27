def format_address(address):
    # Function to format the address for the Google Maps API
    return address.strip().replace(" ", "+")

def handle_api_response(response):
    # Function to handle the response from the Google Maps API
    if response.status == 'OK':
        return response.results[0]
    else:
        raise Exception("Error in API response: " + response.status)