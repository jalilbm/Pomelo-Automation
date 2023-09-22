from requests_html import HTMLSession

session = HTMLSession()

headers = {
    "referer": "https://portal.healthmyself.net/myfamilymd",
    "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    "sec-ch-ua-platform": '"macOS"',
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
}

login_page_response = session.get(
    "https://portal.healthmyself.net/myfamilymd", headers=headers
)

# Extracting tokens from headers
csrf_token = login_page_response.headers.get("x-csrf-token")
xsrf_token = login_page_response.headers.get("x-xsrf-token")

# Saving the content to an HTML file
with open("test.html", "w") as test_file:
    test_file.write(login_page_response.text)
exit()
login_data = {"password": "Watermelon12!4", "email": "drjasonbakermd@gmail.com"}
headers = {
    "authority": "portal.healthmyself.net",
    "accept": "application/json, text/plain, */*",
    "accept-language": "en,ar;q=0.9,fr;q=0.8,en-US;q=0.7,ru;q=0.6",
    "content-type": "application/json;charset=UTF-8",
    #    'cookie': 'io=XaOlz462HkpXQJQXA6N1; AWSALB=7ZtD6JtgHyPWUZHuH34AXWP2CUFOtanii+SGY0p10Qo3pBeiluTHJ7yLQfDeb6P/YMUkZeuGuzW801eM9cl/vwZWF5h5JkHunG7EZuUScFs0cgDnARq2RkR3CxOt; AWSALBCORS=7ZtD6JtgHyPWUZHuH34AXWP2CUFOtanii+SGY0p10Qo3pBeiluTHJ7yLQfDeb6P/YMUkZeuGuzW801eM9cl/vwZWF5h5JkHunG7EZuUScFs0cgDnARq2RkR3CxOt; XSRF-TOKEN=eyJpdiI6ImhNT0RBcXJkdzRDb0RLZUF1Q3cyU0E9PSIsInZhbHVlIjoiRHEyVUFXcEJNQ2VyS1JZUTFtbDZacTlpUTNnWHJxZlp5dEhNR2IxclwvcHEySmh2NFNnaFJ2d2NObmNCVkZSYmYiLCJtYWMiOiI3MjBmZjc0OTBmMmY4ZjYwMTMzNDY2OTk4ZmRhZmVmNjRjMWE1N2UyMjI1MWFlZTlhNzE1MTc0YzlkNDdkOTgyIn0%3D; hm_session=eyJpdiI6IlBXRmQ4VVZxMG13MjRReXNzUFZzSXc9PSIsInZhbHVlIjoiUWd4SFVtaHBGZ3hyS01qQjVpd0hmY2RsWmhKZDF3R3krZkZwRmRTcnJkXC9zd0oxcDlRRm9HaUpzc2ZWaUFyUmoiLCJtYWMiOiI4NGYzMmIyN2IyZTRlYjA1ZjIwY2I2MmI0NWE2MzgyZGY3ZDJkZDg1ZDk5NDIwYWRkYzdkZDRkODYwZTAxNmI5In0%3D; locale=eyJpdiI6InFOSCtMTGhEa1VKbnY3QlVVXC9UYTZnPT0iLCJ2YWx1ZSI6IjdXdTZIZ1JGQTcrQ05IVFozaVQ0blE9PSIsIm1hYyI6ImNkOGMzMjk3OTM2MzQ2YWE4ZDUxNGYzMGI4Yjc5NDU2MzU0MTYxOTZlNTNhZDBjYTgzMWIwOWZiOWVjYTkwYTAifQ%3D%3D',
    "origin": "https://portal.healthmyself.net",
    "referer": "https://portal.healthmyself.net/myfamilymd",
    "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    #    'x-csrf-token': 'K39TVuKeTFiRSRzyA1ljnMDve2guoSz1gpXoUwGf',
    #    'x-hm-client-timezone': 'Asia/Dubai',
    #    'x-requested-with': 'XMLHttpRequest',
    #    'x-xsrf-token': 'eyJpdiI6ImhNT0RBcXJkdzRDb0RLZUF1Q3cyU0E9PSIsInZhbHVlIjoiRHEyVUFXcEJNQ2VyS1JZUTFtbDZacTlpUTNnWHJxZlp5dEhNR2IxclwvcHEySmh2NFNnaFJ2d2NObmNCVkZSYmYiLCJtYWMiOiI3MjBmZjc0OTBmMmY4ZjYwMTMzNDY2OTk4ZmRhZmVmNjRjMWE1N2UyMjI1MWFlZTlhNzE1MTc0YzlkNDdkOTgyIn0='
}
login_response = session.post(
    "https://portal.healthmyself.net/myfamilymd/login", json=login_data, headers=headers
)
print(login_response)
with open("test.html", "w") as test_file:
    test_file.write(login_response.text)
if login_response.status_code == 200:  # or another appropriate condition
    print("Logged in successfully!")
else:
    print("Login failed!")
