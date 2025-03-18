import json

# Your cookies data
cookies_data = [
    {"domain": ".yingjiesheng.com", "expirationDate": 1772760264.497254, "hostOnly": False, "httpOnly": False, "name": "CookieUuid", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "8f10304c302ab8629acc6a8b1b9222e0"},
    # ... other cookies ...
]

# Save cookies to a file
with open("cookies.json", "w") as f:
    json.dump(cookies_data, f)

print("Cookie file created: cookies.json") 