import pandas as pd
import googlemaps
import time
import os

API_KEY = ''


input_file_hanoi = "restaurantsHANOI.csv"
output_file_hanoi = "restaurantsHANOI_google_geocoded.csv"
input_file_oceanpark = "restaurantsOCEANPARK.csv"
output_file_oceanpark = "restaurantsOCEANPARK_google_geocoded.csv"

def geocode_addresses_google(input_file, output_file, api_key):
    try:
        gmaps = googlemaps.Client(key=api_key)
    except Exception as e:
        print(f"Error initializing Google Maps client: {e}")
        return

    try:
        df = pd.read_csv(input_file)
        if 'Address' not in df.columns:
            print(f"Error: 'Address' column not found in {input_file}")
            return

        latitudes = []
        longitudes = []

        print(f"Starting geocoding for {input_file}...")
        for index, row in df.iterrows():
            address = row['Address']
            lat = None
            lng = None
            if isinstance(address, str) and address.strip():
                try:
                    print(f"Geocoding row {index + 1}: {address}")
                    geocode_result = gmaps.geocode(address)

                    if geocode_result and len(geocode_result) > 0:
                        location = geocode_result[0]['geometry']['location']
                        lat = location['lat']
                        lng = location['lng']
                        print(f"  Found: ({lat}, {lng})")
                    else:
                        print("  Not found.")

                    time.sleep(0.1)

                except googlemaps.exceptions.ApiError as e:
                    print(f"  Google Maps API Error for address 	'{address}	': {e}")
                except Exception as e:
                    print(f"  Error geocoding address 	'{address}	': {e}")
            else:
                print(f"Skipping invalid or empty address at row {index + 1}: {address}")

            latitudes.append(lat)
            longitudes.append(lng)

        df['Latitude'] = latitudes
        df['Longitude'] = longitudes
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Successfully processed {input_file} and saved results to {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
    except Exception as e:
        print(f"An unexpected error occurred while processing {input_file}: {e}")

# --- Process Files --- #
print("--- Starting Google Maps Geocoding --- ")
geocode_addresses_google(input_file_hanoi, output_file_hanoi, API_KEY)
geocode_addresses_google(input_file_oceanpark, output_file_oceanpark, API_KEY)
print("--- Google Maps Geocoding process finished --- ")

