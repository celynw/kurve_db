import requests

from kurve_scraper.consts import common_headers


def get_token(username: str, password: str, cookie: str) -> str:
	"""
	Make a POST requesting the access token and return it.

	Parameters
	----------
	username
		Email address
	password
		Password

	Returns
	-------
		Access token

	Raises
	------
	RuntimeError
		Failed to retrieve token
	"""
	url = "https://api.mykurve.com/connect/token"
	headers = common_headers.copy()
	headers["Content-Type"] = "application/x-www-form-urlencoded"
	headers["Content-Length"] = "116"
	headers["Cookie"] = cookie
	headers["Priority"] = "u=0"
	data = {
		"username": username,
		"password": password,
		"grant_type": "password",
		"scope": "api-name",
		"client_id": "ApiClient",
	}

	response = requests.post(url, headers=headers, data=data, timeout=3)

	if response.status_code == 200:
		return response.json()["access_token"]
	raise RuntimeError(f"Failed to retrieve token: {response.status_code}")


def get_account(token: str) -> int:
	url = "https://api.mykurve.com/api/Pages/CustomerAccounts"
	headers = common_headers.copy()
	headers["Authorization"] = f"Bearer {token}"

	response = requests.get(url, headers=headers, timeout=3)

	if response.status_code == 200:
		return int(response.json()["accounts"][0]["accountNumber"])
	raise RuntimeError(f"Failed to retrieve account number: {response.status_code}")
