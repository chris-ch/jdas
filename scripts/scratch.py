"""
Details

Hi, I need data from ONEMAP. Here is the map, https://www.onemap.sg/index.html Here is the API documentation link,
http://www.onemap.sg/api/help/ What data do I need? Valid Postal Codes (Postal Code range is from 000000 - 999999)
Find the valid postal codes.

Then use the valid postal codes to find, Lat Long Building Name Street Name Full Street Address
Example
Postal Code - 410636
Lat - 1.3311 Long - 103.9044
Building Name - EUNOS TENAGA VILLE
Street Name - BEDOK RESERVOIR ROAD
Full Street Address - 636 Bedok Reservoir Road

Bonus, If you scan through the map, you will realize they are using particular colors for particular landscape types.
Example, 636 Bedok Reservoir Road is a HDB Building - They use Yellow. Eunos MRT is a MRT station - They use dull Blue.
Eunos Bus Interchange is a BUS Station - They use Brown. Bayshore Park is a Private Condominium - They use Grey.
Bedok Stadium is a Recreational Place - They use Pink. East Coast Park is a National Park - They use Green.
Ping Yi Secondary School is a School - They use lighter Yellow.
MASJID ABDUL GAFOOR is a Mosque (Place of worship) - they use Light Purple.

Why am i saying this? If you are able to get the full list of available categories of places, it will help us put the
scraped addresses in the right categories. Also, some important places like Bedok Reservoir Park, Admiralty Park,
East Coast Park and more doesn't even have a postal code. So, again if we are able to get the list of categories,
then we will be able to get a better list of places using the categories and places that fall under those categories.
If both can be done, then, we will have a perfect list of places in Singapore. Let me know if you can do this

"""

"""
OneMap http://www.onemap.sg/api/help/
"""
import requests

onemap_key = 'HcDIwzp3nxH+VYi2H9riWofVPGgRhZieeyZ0UX40OxlUlyxQ2tSpc0xfnkSfPitdNkzENMl8QKG2aitHSokYriHnaACPNGZp|mv73ZvjFcSo='

temp_key_url = 'http://www.onemap.sg/API/services.svc/getToken?accessKEY=%s' % onemap_key

response = requests.get(temp_key_url, data=dict())
new_token = response.json()['GetToken'][0]['NewToken']
