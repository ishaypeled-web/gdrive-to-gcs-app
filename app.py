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
    """Test connection to Google services with provided credentials"""
    try:
        # Get form data
        client_id = request.form.get('client_id', '').strip()
        client_secret = request.form.get('client_secret', '').strip()
        oauth_project_id = request.form.get('oauth_project_id', '').strip()
        gcs_project_id = request.form.get('gcs_project_id', '').strip()
        gcs_bucket_name = request.form.get('gcs_bucket_name', '').strip()
        service_account_key = request.form.get('service_account_key', '').strip()

        if not all([client_id, client_secret, oauth_project_id, gcs_project_id, gcs_bucket_name, service_account_key]):
            return jsonify({'success': False, 'error': 'כל השדות נדרשים'})

        # Test service account credentials
        try:
            sa_credentials = create_service_account_credentials(service_account_key)
            storage_client = storage.Client(project=gcs_project_id, credentials=sa_credentials)
            
            # Test bucket access
            bucket = storage_client.bucket(gcs_bucket_name)
            bucket.reload()  # This will raise an exception if bucket doesn't exist or no access
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'שגיאה ב-Service Account או באקט: {str(e)}'})

        # Test OAuth configuration (just validate format)
        try:
            redirect_uri = "https://gdrive-to-gcs-app-850086889211.us-central1.run.app/oauth2callback"
            flow = create_oauth_flow(client_id, client_secret, oauth_project_id, redirect_uri)
        except Exception as e:
            return jsonify({'success': False, 'error': f'שגיאה בהגדרות OAuth: {str(e)}'})

        return jsonify({'success': True, 'message': 'כל החיבורים תקינים!'})

    except Exception as e:
        return jsonify({'success': False, 'error': f'שגיאה כללית: {str(e)}'})

@app.route('/authorize', methods=['GET', 'POST'])
@app.route('/transfer', methods=['GET', 'POST'])
def authorize():
    """Start OAuth authorization with provided credentials"""
    try:
        # Handle GET request - redirect to home page
        if request.method == 'GET':
            flash('אנא מלא את הטופס תחילה', 'warning')
            return redirect(url_for('index'))
        
        # Store credentials in session (POST request)
        session['client_id'] = request.form.get('client_id', '').strip()
        session['client_secret'] = request.form.get('client_secret', '').strip()
        session['oauth_project_id'] = request.form.get('oauth_project_id', '').strip()
        session['gcs_project_id'] = request.form.get('gcs_project_id', '').strip()
        session['gcs_bucket_name'] = request.form.get('gcs_bucket_name', '').strip()
        session['service_account_key'] = request.form.get('service_account_key', '').strip()
        session['drive_folder_id'] = request.form.get('drive_folder_id', '').strip()

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
        return redirect(authorization_url)

    except Exception as e:
        flash(f'שגיאה באימות: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback"""
    try:
        state = session.get('state')
        if not state:
            flash('שגיאה: מצב אימות לא תקין', 'error')
            return redirect(url_for('index'))

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
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials
        credentials = flow.credentials
        session['drive_credentials'] = credentials_to_dict(credentials)
        
        flash('התחברת בהצלחה ל-Google Drive!', 'success')
        return redirect(url_for('start_transfer'))

    except Exception as e:
        flash(f'שגיאה בהשלמת האימות: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/transfer-auto')
def transfer_files_auto():
    """Perform actual file transfer after OAuth completion"""
    try:
        # Get credentials from session
        drive_credentials_dict = session.get('drive_credentials')
        if not drive_credentials_dict:
            flash('יש להתחבר תחילה ל-Google Drive', 'error')
            return redirect(url_for('index'))

        # Get other parameters from session
        drive_folder_id = session.get('drive_folder_id')
        gcs_bucket_name = session.get('gcs_bucket_name')
        gcs_project_id = session.get('gcs_project_id')
        service_account_key = session.get('service_account_key')

        if not all([drive_folder_id, gcs_bucket_name, gcs_project_id, service_account_key]):
            flash('חסרים פרטים נדרשים', 'error')
            return redirect(url_for('index'))

        # Create Drive credentials
        drive_creds = Credentials(**drive_credentials_dict)
        drive_service = build('drive', 'v3', credentials=drive_creds)
        
        # Create GCS credentials
        sa_credentials = create_service_account_credentials(service_account_key)
        storage_client = storage.Client(project=gcs_project_id, credentials=sa_credentials)

        # List files in Google Drive folder
        results = drive_service.files().list(
            q=f"'{drive_folder_id}' in parents and trashed=false",
            fields="files(id, name, size, mimeType)"
        ).execute()
        items = results.get('files', [])

        if not items:
            flash('לא נמצאו קבצים בתיקיית Google Drive שצוינה', 'warning')
            return redirect(url_for('index'))

        # Get bucket
        try:
            bucket = storage_client.bucket(gcs_bucket_name)
            bucket.reload()
        except Exception:
            flash(f'הבאקט {gcs_bucket_name} לא נמצא או לא נגיש', 'error')
            return redirect(url_for('index'))

        transferred_files = []
        transfer_start = datetime.now()

        # Transfer files to GCS
        for item in items:
            try:
                file_id = item['id']
                file_name = item['name']
                
                # Skip Google Docs native formats
                if item.get('mimeType', '').startswith('application/vnd.google-apps'):
                    transferred_files.append({
                        'name': file_name,
                        'size': 'N/A',
                        'status': 'skipped',
                        'error': 'Google Docs format - skipped'
                    })
                    continue

                # Download from Drive
                request_file = drive_service.files().get_media(fileId=file_id)
                file_content = request_file.execute()

                # Upload to GCS
                blob = bucket.blob(file_name)
                blob.upload_from_string(file_content)

                transferred_files.append({
                    'name': file_name,
                    'size': item.get('size', 'Unknown'),
                    'status': 'success'
                })

            except Exception as e:
                transferred_files.append({
                    'name': item.get('name', 'Unknown'),
                    'size': item.get('size', 'Unknown'),
                    'status': 'error',
                    'error': str(e)
                })

        transfer_end = datetime.now()
        transfer_duration = transfer_end - transfer_start

        return render_template('result.html',
                             drive_folder_id=drive_folder_id,
                             gcs_bucket_name=gcs_bucket_name,
                             project_id=gcs_project_id,
                             files=transferred_files,
                             files_count=len([f for f in transferred_files if f['status'] == 'success']),
                             transfer_time=str(transfer_duration).split('.')[0])

    except HttpError as e:
        flash(f'שגיאה ב-Google API: {str(e)}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'שגיאה כללית: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/status')
def status():
    """API endpoint to check authentication status"""
    drive_credentials = session.get('drive_credentials')
    return jsonify({
        'authenticated': drive_credentials is not None,
        'drive_connected': drive_credentials is not None
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    flash('שגיאה פנימית בשרת', 'error')
    return render_template('index.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
