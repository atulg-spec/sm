import requests
from ipware import get_client_ip as ipware_get_client_ip

def get_client_ip_address(request):
    """
    Retrieves the client IP address from the request using django-ipware.
    """
    client_ip, is_routable = ipware_get_client_ip(request)
    if client_ip is None:
        return None
    return client_ip

def get_geo_data(ip_address):
    """
    Fetches geolocation data for the given IP address using ip-api.com.
    Returns a dictionary of data or None if failed.
    """
    if not ip_address:
        return None
        
    # ip-api.com endpoint
    url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'success':
            return data
        else:
            # Log error if needed: data.get('message')
            return None
    except requests.RequestException:
        return None

def update_user_ip_info(user, request):
    """
    Updates the user's profile with IP and GeoIP data.
    """
    from .models import UserProfile
    
    ip = get_client_ip_address(request)
    if not ip:
        return

    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Check if IP changed or if it's a fresh profile with no IP
    if profile.ip_address != ip:
        profile.ip_address = ip
        
        # Fetch Geo Data
        geo_data = get_geo_data(ip)
        
        if geo_data:
            profile.country = geo_data.get('country')
            profile.region = geo_data.get('regionName')
            profile.city = geo_data.get('city')
            profile.zip_code = geo_data.get('zip')
            profile.lat = geo_data.get('lat')
            profile.lon = geo_data.get('lon')
            profile.isp = geo_data.get('isp')
            profile.timezone = geo_data.get('timezone')
            
            # Construct Google Maps Link
            if profile.lat and profile.lon:
                profile.map_link = f"https://www.google.com/maps/search/?api=1&query={profile.lat},{profile.lon}"
        
        profile.save()
