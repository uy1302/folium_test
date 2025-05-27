import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import os

geolocator = Nominatim(user_agent="manus_geocoder_1.0")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

input_file_hanoi = "restaurantsHANOI.csv"
output_file_hanoi = "restaurantsOCEANPARK.csv"
input_file_oceanpark = "restaurantsOCEANPARK_new.csv"
output_file_oceanpark = "restaurantsOCEANPARK_geocoded_new.csv"

def geocode_addresses(input_file, output_file):
    try:
        df = pd.read_csv(input_file)
        if 'Address' not in df.columns:
            print(f"Error: 'Address' column not found in {input_file}")
            return

        latitudes = []
        longitudes = []

        for address in df['Address']:
            location = None
            try:
                full_address = address
                if isinstance(address, str):
                    if 'Việt Nam' not in address and 'Vietnam' not in address and ('Hà Nội' in address or 'Gia Lâm' in address):
                        full_address = address + ", Việt Nam"
                    print(f"Geocoding: {full_address}")
                    location = geocode(full_address, timeout=10)
                else:
                    print(f"Skipping invalid address: {address}")

                if location:
                    latitudes.append(location.latitude)
                    longitudes.append(location.longitude)
                    print(f"Found: ({location.latitude}, {location.longitude})")
                else:
                    latitudes.append(None)
                    longitudes.append(None)
                    print("Not found.")
            except Exception as e:
                print(f"Error geocoding '{address}': {e}")
                latitudes.append(None)
                longitudes.append(None)

        df['Latitude'] = latitudes
        df['Longitude'] = longitudes
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Successfully processed {input_file} and saved results to {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
    except Exception as e:
        print(f"An unexpected error occurred while processing {input_file}: {e}")

print(f"Processing {input_file_hanoi}...")
geocode_addresses(input_file_hanoi, output_file_hanoi)

print(f"\nProcessing {input_file_oceanpark}...")
geocode_addresses(input_file_oceanpark, output_file_oceanpark)

print("\nGeocoding process completed for both files.")

