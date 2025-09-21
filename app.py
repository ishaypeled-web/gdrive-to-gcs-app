import os
import io
import json
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

def create_oauth_flow(client_id, client_secret, project_id, redirect_uri):
    """Create OAuth flow from provided credentials"""
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "project_id": project_id,
            "redirect_uris": [redirect_uri]
        }
    }
    
    return Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/drive.readonly'],
        redirect_uri=redirect_uri
    )

def create_service_account_credentials(service_account_json):
    """Create service account credentials from JSON string"""
    try:
        service_account_info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        return credentials
    except Exception as e:
        raise ValueError(f"Invalid service account JSON: {str(e)}")

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection with provided credentials"""
    try:
        # Test OAuth credentials
        client_id = request.form.get('client_id', '').strip()
        client_secret = request.form.get('client_secret', '').strip()
        oauth_project_id = request.form.get('oauth_project_id', '').strip()
        
        if not all([client_id, client_secret, oauth_project_id]):
            return jsonify({'success': False, 'message': 'חסרים פרטי OAuth'})
        
        # Test service account
        service_account_key = request.form.get('service_account_key', '').strip()
        gcs_project_id = request.form.get('gcs_project_id', '').strip()
        
        if not all([service_account_key, gcs_project_id]):
            return jsonify({'success': False, 'message': 'חסרים פרטי Service Account'})
        
        # Test service account JSON
        try:
            create_service_account_credentials(service_account_key)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Service Account לא תקין: {str(e)}'})
        
        # Test bucket access
        gcs_bucket_name = request.form.get('gcs_bucket_name', '').strip()
        if gcs_bucket_name:
            try:
                sa_credentials = create_service_account_credentials(service_account_key)
                storage_client = storage.Client(project=gcs_project_id, credentials=sa_credentials)
                bucket = storage_client.bucket(gcs_bucket_name)
                bucket.reload()
            except Exception as e:
                return jsonify({'success': False, 'message': f'לא ניתן לגשת לבאקט: {str(e)}'})
        
        return jsonify({'success': True, 'message': 'כל החיבורים תקינים!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'שגיאה: {str(e)}'})

@app.route('/authorize', methods=['GET', 'POST'])
@app.route('/transfer', methods=['GET', 'POST'])
def authorize():
    """Start OAuth authorization with provided credentials"""
    try:
        # Handle GET request - redirect to home page
        if request.method == 'GET':
            flash('אנא מלא את הטופס תחילה', 'warning')
            return redirect(url_for('index'))
        
        print("=== DEBUG: Starting authorize function ===")
        
        # Store credentials in session (POST request)
        session['client_id'] = request.form.get('client_id', '').strip()
        session['client_secret'] = request.form.get('client_secret', '').strip()
        session['oauth_project_id'] = request.form.get('oauth_project_id', '').strip()
        session['gcs_project_id'] = request.form.get('gcs_project_id', '').strip()
        session['gcs_bucket_name'] = request.form.get('gcs_bucket_name', '').strip()
        session['service_account_key'] = request.form.get('service_account_key', '').strip()
        session['drive_folder_id'] = request.form.get('drive_folder_id', '').strip()

        print(f"DEBUG: Stored in session:")
        print(f"  client_id: {session.get('client_id', 'MISSING')[:20]}...")
        print(f"  drive_folder_id: {session.get('drive_folder_id', 'MISSING')}")
        print(f"  gcs_bucket_name: {session.get('gcs_bucket_name', 'MISSING')}")
        print(f"  gcs_project_id: {session.get('gcs_project_id', 'MISSING')}")

        # Create OAuth flow
        redirect_uri = "https://gdrive-to-gcs-app-850086889211.us-central1.run.app/oauth2callback"
        flow = create_oauth_flow(
            session['client_id'],
            session['client_secret'],
            session['oauth_project_id'],
            redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        session['state'] = state
        print(f"DEBUG: OAuth state: {state}")
        print(f"DEBUG: Redirecting to: {authorization_url}")
        
        return redirect(authorization_url)

    except Exception as e:
        print(f"DEBUG: Error in authorize: {str(e)}")
        flash(f'שגיאה באימות: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback"""
    try:
        print("=== DEBUG: Starting oauth2callback ===")
        
        state = session.get('state')
        if not state:
            print("DEBUG: No state in session")
            flash('שגיאה: מצב אימות לא תקין', 'error')
            return redirect(url_for('index'))

        print(f"DEBUG: State from session: {state}")
        print(f"DEBUG: Session contents: {list(session.keys())}")

        # Recreate flow
        redirect_uri = "https://gdrive-to-gcs-app-850086889211.us-central1.run.app/oauth2callback"
        flow = create_oauth_flow(
            session['client_id'],
            session['client_secret'],
            session['oauth_project_id'],
            redirect_uri
        )
        flow.state = state

        # Fetch token
        authorization_response = request.url
        print(f"DEBUG: Authorization response URL: {authorization_response}")
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials
        credentials = flow.credentials
        session['drive_credentials'] = credentials_to_dict(credentials)
        
        print("DEBUG: Drive credentials stored successfully")
        flash('התחברת בהצלחה ל-Google Drive!', 'success')
        
        print("DEBUG: Redirecting to transfer_files_auto")
        return redirect(url_for('transfer_files_auto'))

    except Exception as e:
        print(f"DEBUG: Error in oauth2callback: {str(e)}")
        flash(f'שגיאה בהשלמת האימות: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/transfer-auto')
def transfer_files_auto():
    """Perform actual file transfer after OAuth completion"""
    try:
        print("=== DEBUG: Starting transfer_files_auto ===")
        print(f"DEBUG: Session keys: {list(session.keys())}")
        
        # Get credentials from session
        drive_credentials_dict = session.get('drive_credentials')
        if not drive_credentials_dict:
            print("DEBUG: No drive_credentials in session")
            flash('יש להתחבר תחילה ל-Google Drive', 'error')
            return redirect(url_for('index'))

        print("DEBUG: Drive credentials found")

        # Get other parameters from session
        drive_folder_id = session.get('drive_folder_id')
        gcs_bucket_name = session.get('gcs_bucket_name')
        gcs_project_id = session.get('gcs_project_id')
        service_account_key = session.get('service_account_key')

        print(f"DEBUG: Parameters from session:")
        print(f"  drive_folder_id: {drive_folder_id}")
        print(f"  gcs_bucket_name: {gcs_bucket_name}")
        print(f"  gcs_project_id: {gcs_project_id}")
        print(f"  service_account_key: {'Present' if service_account_key else 'Missing'}")

        if not all([drive_folder_id, gcs_bucket_name, gcs_project_id, service_account_key]):
            missing = []
            if not drive_folder_id: missing.append('drive_folder_id')
            if not gcs_bucket_name: missing.append('gcs_bucket_name')
            if not gcs_project_id: missing.append('gcs_project_id')
            if not service_account_key: missing.append('service_account_key')
            
            print(f"DEBUG: Missing parameters: {missing}")
            flash(f'חסרים פרטים נדרשים: {", ".join(missing)}', 'error')
            return redirect(url_for('index'))

        print("DEBUG: All parameters present, starting transfer...")

        # Create Drive credentials
        drive_creds = Credentials(**drive_credentials_dict)
        drive_service = build('drive', 'v3', credentials=drive_creds)
        
        # Create GCS credentials
        sa_credentials = create_service_account_credentials(service_account_key)
        storage_client = storage.Client(project=gcs_project_id, credentials=sa_credentials)

        # List files in Google Drive folder
        print(f"DEBUG: Listing files in Drive folder: {drive_folder_id}")
        results = drive_service.files().list(
            q=f"'{drive_folder_id}' in parents and trashed=false",
            fields="files(id, name, size, mimeType)"
        ).execute()
        items = results.get('files', [])

        print(f"DEBUG: Found {len(items)} files in Drive folder")

        if not items:
            flash('לא נמצאו קבצים בתיקיית Google Drive שצוינה', 'warning')
            return redirect(url_for('index'))

        # Get bucket
        try:
            print(f"DEBUG: Accessing GCS bucket: {gcs_bucket_name}")
            bucket = storage_client.bucket(gcs_bucket_name)
            bucket.reload()
            print("DEBUG: Bucket access successful")
        except Exception as e:
            print(f"DEBUG: Bucket access failed: {str(e)}")
            flash(f'הבאקט {gcs_bucket_name} לא נמצא או לא נגיש: {str(e)}', 'error')
            return redirect(url_for('index'))

        transferred_files = []
        transfer_start = datetime.now()

        # Transfer files to GCS
        for i, item in enumerate(items):
            try:
                file_id = item['id']
                file_name = item['name']
                
                print(f"DEBUG: Processing file {i+1}/{len(items)}: {file_name}")
                
                # Skip Google Docs native formats
                if item.get('mimeType', '').startswith('application/vnd.google-apps'):
                    print(f"DEBUG: Skipping Google Docs format: {file_name}")
                    transferred_files.append({
                        'name': file_name,
                        'size': 'N/A',
                        'status': 'skipped',
                        'error': 'Google Docs format - skipped'
                    })
                    continue

                # Download from Drive
                print(f"DEBUG: Downloading from Drive: {file_name}")
                request_file = drive_service.files().get_media(fileId=file_id)
                file_content = request_file.execute()

                # Upload to GCS
                print(f"DEBUG: Uploading to GCS: {file_name}")
                blob = bucket.blob(file_name)
                blob.upload_from_string(file_content)

                print(f"DEBUG: Successfully transferred: {file_name}")
                transferred_files.append({
                    'name': file_name,
                    'size': item.get('size', 'Unknown'),
                    'status': 'success'
                })

            except Exception as e:
                print(f"DEBUG: Error transferring {item.get('name', 'Unknown')}: {str(e)}")
                transferred_files.append({
                    'name': item.get('name', 'Unknown'),
                    'size': item.get('size', 'Unknown'),
                    'status': 'error',
                    'error': str(e)
                })

        transfer_end = datetime.now()
        transfer_duration = transfer_end - transfer_start

        print(f"DEBUG: Transfer completed. Success: {len([f for f in transferred_files if f['status'] == 'success'])}")

        return render_template('result.html',
                             drive_folder_id=drive_folder_id,
                             gcs_bucket_name=gcs_bucket_name,
                             project_id=gcs_project_id,
                             files=transferred_files,
                             files_count=len([f for f in transferred_files if f['status'] == 'success']),
                             transfer_time=str(transfer_duration).split('.')[0])

    except HttpError as e:
        print(f"DEBUG: Google API Error: {str(e)}")
        flash(f'שגיאה ב-Google API: {str(e)}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        print(f"DEBUG: General Error: {str(e)}")
        flash(f'שגיאה כללית: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/status')
def status():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
