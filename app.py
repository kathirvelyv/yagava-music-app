from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import boto3
from botocore.config import Config
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
        MAX_CONTENT_LENGTH=200 * 1024 * 1024,  # 200MB max file size (increased for large audio files)
        ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD', 'admin123'),  # Set your admin password in .env
        SESSION_COOKIE_SECURE=False,  # Allow cookies over HTTP for local dev
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax'
    )
    
    # No file logging handler
    
    # Initialize Filebase S3 client
    s3_client = boto3.client('s3',
        endpoint_url='https://s3.filebase.com',
        aws_access_key_id=os.getenv('FILEBASE_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('FILEBASE_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    # Make S3 client available to all routes
    app.s3_client = s3_client
    app.config['BUCKET_NAME'] = os.getenv('FILEBASE_BUCKET_NAME')
    
    return app

# Initialize Flask application
app = create_app()

# Constants
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return redirect(url_for('player'))

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
                password = data.get('password')
            else:
                password = request.form.get('password')
            if not password:
                if request.is_json:
                    return jsonify({'error': 'Password is required'}), 400
                else:
                    error = 'Password is required'
            elif password == app.config['ADMIN_PASSWORD']:
                if request.is_json:
                    response = jsonify({'message': 'Login successful'})
                    response.set_cookie('is_admin', 'true', samesite='Lax')
                    app.logger.info('Admin logged in successfully')
                    return response
                else:
                    from flask import make_response
                    response = make_response(redirect(url_for('upload_page')))
                    response.set_cookie('is_admin', 'true', samesite='Lax')
                    app.logger.info('Admin logged in successfully')
                    return response
            else:
                if request.is_json:
                    return jsonify({'error': 'Invalid password'}), 401
                else:
                    error = 'Invalid password'
        except Exception as e:
            app.logger.error(f'Admin login error: {str(e)}')
            if request.is_json:
                return jsonify({'error': 'An error occurred during login'}), 500
            else:
                error = 'An error occurred during login'
    return render_template('admin_login.html', error=error)

@app.route('/admin-logout', methods=['POST'])
def admin_logout():
    try:
        response = jsonify({'message': 'Logout successful'})
        response.delete_cookie('is_admin')
        app.logger.info('Admin logged out')
        return response
    except Exception as e:
        app.logger.error(f'Admin logout error: {str(e)}')
        return jsonify({'error': 'An error occurred during logout'}), 500

@app.route('/player')
def player():
    return render_template('player.html', is_admin=request.cookies.get('is_admin') == 'true')

# OPTIONAL: Separate upload page for admins
@app.route('/upload-page')
def upload_page():
    """Dedicated upload page (optional - upload is also available in player)"""
    return render_template('upload.html', is_admin=request.cookies.get('is_admin') == 'true')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.cookies.get('is_admin') != 'true':
        return jsonify({'error': 'Unauthorized'}), 401
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_key = filename  # Files in root folder (changed from music/)
            
            # Upload to Filebase
            app.s3_client.upload_fileobj(file, app.config['BUCKET_NAME'], file_key)
            
            app.logger.info(f'File uploaded: {filename} by admin')
            return jsonify({'message': 'File uploaded successfully'})
            
        except Exception as e:
            app.logger.error(f'Upload error: {str(e)}')
            return jsonify({'error': 'Failed to upload file'}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/test-filebase')
def test_filebase():
    try:
        # Test bucket access
        app.logger.info(f"Testing connection to bucket: {app.config['BUCKET_NAME']}")
        response = app.s3_client.list_objects_v2(
            Bucket=app.config['BUCKET_NAME'],
            MaxKeys=1
        )
        app.logger.info(f"Connection successful. Response: {response}")
        return jsonify({
            'status': 'success',
            'message': 'Filebase connection successful',
            'bucket': app.config['BUCKET_NAME'],
            'response': response
        })
    except Exception as e:
        app.logger.error(f'Filebase connection error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'Filebase connection failed: {str(e)}',
            'bucket': app.config['BUCKET_NAME']
        }), 500

@app.route('/music-list')
def get_music_list():
    try:
        app.logger.info(f"Fetching music from bucket: {app.config['BUCKET_NAME']}")
        response = app.s3_client.list_objects_v2(
            Bucket=app.config['BUCKET_NAME']
            # Removed Prefix - list all files in root
        )
        
        song_list = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                # Skip folders and only get audio files
                if obj['Key'].lower().endswith(tuple(ALLOWED_EXTENSIONS)):
                    try:
                        # Generate a pre-signed URL that's valid for 1 hour
                        url = app.s3_client.generate_presigned_url('get_object',
                            Params={
                                'Bucket': app.config['BUCKET_NAME'],
                                'Key': obj['Key']
                            },
                            ExpiresIn=3600
                        )
                        
                        # Get the filename without extension
                        filename = obj['Key']
                        title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
                        
                        song_list.append({
                            'name': title,
                            'url': url
                        })
                        app.logger.info(f"Added song to list: {title}")
                    except Exception as song_error:
                        app.logger.error(f"Error processing song {obj['Key']}: {str(song_error)}")
                        continue
        
        return jsonify(song_list)
        
    except Exception as e:
        app.logger.error(f'Error fetching music list: {str(e)}')
        # Log more details about the error
        import traceback
        app.logger.error(f'Detailed error: {traceback.format_exc()}')
        return jsonify({
            'error': 'Failed to fetch music list',
            'details': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Production server configuration
    from waitress import serve
    serve(app, host='0.0.0.0', port=5006)