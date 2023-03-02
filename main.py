from flask import Flask, render_template, request, redirect
from requests_oauthlib import OAuth2Session
import requests, json, uuid
from utils import upload_blob_from_memory, find_link, add_qs_params

SCOPES_TO_REQUEST = {'offline_access', 'ag1', 'ag2', 'ag3', 'eq1', 'files'}
WELL_KNOWN_URL = 'https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/.well-known/oauth-authorization-server'
MYJOHNDEERE_V3_JSON_HEADERS = { 'Accept': 'application/vnd.deere.axiom.v3+json',
                                'Content-Type': 'application/vnd.deere.axiom.v3+json'}

# If your app happens to be already approved for production, then use the partnerapi.deere.com, otherwise stick with sandboxapi.deere.com
API_CATALOG_URI = 'https://sandboxapi.deere.com/platform/'
#API_CATALOG_URI = 'https://partnerapi.deere.com/platform/'

# Query the ./well-known OAuth URL and parse out the authorization URL, the token grant URL, and the available scopes
well_known_response = requests.get(WELL_KNOWN_URL)
well_known_info = json.loads(well_known_response.text)
AUTHORIZATION_ENDPOINT = well_known_info['authorization_endpoint']
TOKEN_GRANT_URL = well_known_info['token_endpoint']

app = Flask(__name__)
app.config.from_pyfile('settings.py')

oauth2_session = OAuth2Session(app.config.get("CLIENT_ID"),  redirect_uri=app.config.get("CLIENT_REDIRECT_URI"), scope=SCOPES_TO_REQUEST)

def check_connections(organizations_link):
  # Look for a connections link
  response = oauth2_session.get(organizations_link, headers = MYJOHNDEERE_V3_JSON_HEADERS)
  if response.status_code == 200:
    organizations = response.json()
    for org in organizations['values']:
      connection = find_link(org['links'], 'connections')
      if connection: return connection
    next_link = find_link(organizations['links'], 'nextPage')
    if next_link: check_connections(next_link)
    else: return False
  else: return False

@app.route('/')
def index():
  authorization_request, state = oauth2_session.authorization_url(AUTHORIZATION_ENDPOINT, str(uuid.uuid4()))
  return render_template('index.html', authorization_request=authorization_request)

@app.route('/callback')
def callback():
  args = request.args
  if args.get('code'):
    token_response = oauth2_session.fetch_token(TOKEN_GRANT_URL, code=args.get('code'), client_secret=app.config.get("CLIENT_SECRET"))
    access_token = token_response['access_token']
    refresh_token = token_response['refresh_token']
    access_token_expiration = token_response['expires_in']

    contents = f"Access Token: {access_token}\nRefresh token: {refresh_token}\nHours Token Is Valid: {str(int(access_token_expiration/60/60))}"
    upload_blob_from_memory(app.config.get("BUCKET_NAME"), contents, f'taranis/johndeere/{str(uuid.uuid4())}.txt')

    api_catalog_response = oauth2_session.get(API_CATALOG_URI, headers=MYJOHNDEERE_V3_JSON_HEADERS)
    if api_catalog_response.status_code == 200:
      api_catalog_response = api_catalog_response.json() 
      organizations_link = find_link(api_catalog_response['links'], 'organizations')
      connections_link = check_connections(organizations_link)

      if connections_link: return redirect(add_qs_params(connections_link, {'redirect_uri':app.config.get('CLIENT_REDIRECT_URI')}))

  return redirect('/success')

@app.route('/success')
def success():
  return render_template('success.html')