import pyotp
import requests

from kurve_scraper.consts import common_headers


def get_token(username: str, password: str, totp_secret: str = "") -> str:
	"""
	Make a POST requesting the access token and return it.

	Parameters
	----------
	username
		Email address
	password
		Password
	totp_secret: optional
		Two-factor authentication secret

	Returns
	-------
		Access token

	Raises
	------
	RuntimeError
		Failed to retrieve token
	"""
	s = requests.Session()
	s.headers.update(common_headers)

	data = {
		"username": username,
		"password": password,
		"grant_type": "password",
		"scope": "api-name",
		"client_id": "ApiClient",
	}

	# Initial request
	r1 = s.post("https://api.mykurve.com/connect/token", data=data)
	if r1.status_code == 200:
		return r1.json()["access_token"]

	# Check if MFA is required
	if r1.status_code == 400 and "mfaCode required" in r1.text:
		if not totp_secret:
			raise RuntimeError("MFA code required, but no TOTP secret provided.")
		totp = pyotp.TOTP(totp_secret)
		data["mfaCode"] = totp.now()
		r2 = s.post("https://api.mykurve.com/connect/token", data=data)
		if r2.status_code == 200:
			return r2.json()["access_token"]
		raise RuntimeError(f"Failed to retrieve access token with MFA: {r2.status_code} {r2.text}")

	raise RuntimeError(f"Failed to retrieve access token: {r1.status_code} {r1.text}")


def get_account(token: str) -> int:
	url = "https://api.mykurve.com/api/Pages/CustomerAccounts"
	headers = common_headers.copy()
	headers["Authorization"] = f"Bearer {token}"

	response = requests.get(url, headers=headers, timeout=3)

	if response.status_code == 200:
		return int(response.json()["accounts"][0]["accountNumber"])
	raise RuntimeError(f"Failed to retrieve account number: {response.status_code}")
