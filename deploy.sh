#!/bin/bash

# סקריפט פריסה אוטומטי לאפליקציית העברת קבצים מ-Google Drive ל-GCS
# Google Drive to GCS Transfer App - Automated Deployment Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_prerequisites() {
    print_status "בדיקת דרישות מוקדמות..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK לא מותקן. אנא התקן אותו מ: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! command -v zip &> /dev/null; then
        print_error "zip לא מותקן. אנא התקן אותו."
        exit 1
    fi
    
    print_success "כל הדרישות המוקדמות מותקנות"
}

# Get project configuration
get_project_config() {
    print_status "קבלת הגדרות פרויקט..."
    
    # Get current project
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "לא נמצא פרויקט פעיל. אנא הגדר פרויקט:"
        echo "gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
    
    print_success "פרויקט פעיל: $PROJECT_ID"
    
    # Set default values
    SERVICE_NAME=${SERVICE_NAME:-"gdrive-to-gcs-app"}
    REGION=${REGION:-"us-central1"}
    
    print_status "שם שירות: $SERVICE_NAME"
    print_status "אזור: $REGION"
}

# Enable required APIs
enable_apis() {
    print_status "הפעלת APIs נדרשים..."
    
    APIS=(
        "run.googleapis.com"
        "cloudbuild.googleapis.com"
        "containerregistry.googleapis.com"
        "drive.googleapis.com"
        "storage.googleapis.com"
    )
    
    for api in "${APIS[@]}"; do
        print_status "מפעיל $api..."
        gcloud services enable "$api" --quiet
    done
    
    print_success "כל ה-APIs הופעלו בהצלחה"
}

# Check for client secrets file
check_client_secrets() {
    print_status "בדיקת קובץ client_secrets.json..."
    
    if [ ! -f "client_secrets.json" ]; then
        print_warning "קובץ client_secrets.json לא נמצא"
        print_status "אנא:"
        echo "1. עבור אל https://console.cloud.google.com/apis/credentials"
        echo "2. צור OAuth 2.0 Client ID"
        echo "3. הורד את קובץ ה-JSON ושמור אותו בשם client_secrets.json"
        echo "4. הרץ את הסקריפט שוב"
        exit 1
    fi
    
    print_success "קובץ client_secrets.json נמצא"
}

# Deploy to Cloud Run
deploy_app() {
    print_status "מתחיל פריסה ל-Cloud Run..."
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -base64 32)
    
    # Deploy using source-based deployment
    gcloud run deploy "$SERVICE_NAME" \
        --source . \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --set-env-vars "SECRET_KEY=$SECRET_KEY" \
        --set-env-vars "CLIENT_SECRETS_FILE=client_secrets.json" \
        --memory 512Mi \
        --cpu 1 \
        --timeout 300 \
        --max-instances 10 \
        --quiet
    
    print_success "פריסה הושלמה בהצלחה!"
}

# Get service URL
get_service_url() {
    print_status "קבלת URL השירות..."
    
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region "$REGION" \
        --format 'value(status.url)')
    
    if [ -n "$SERVICE_URL" ]; then
        print_success "השירות זמין בכתובת: $SERVICE_URL"
        print_warning "אל תשכח לעדכן את ה-OAuth redirect URI ל: $SERVICE_URL/oauth2callback"
    else
        print_error "לא הצלחתי לקבל את URL השירות"
    fi
}

# Main deployment function
main() {
    echo "=================================================="
    echo "  אפליקציית העברת קבצים מ-Google Drive ל-GCS"
    echo "  Google Drive to GCS Transfer App"
    echo "=================================================="
    echo
    
    check_prerequisites
    get_project_config
    enable_apis
    check_client_secrets
    deploy_app
    get_service_url
    
    echo
    print_success "הפריסה הושלמה בהצלחה!"
    echo
    print_status "שלבים נוספים:"
    echo "1. עדכן את ה-OAuth redirect URI ב-Google Cloud Console"
    echo "2. בדוק שהבאקט ב-GCS קיים ונגיש"
    echo "3. נסה את האפליקציה בכתובת: $SERVICE_URL"
    echo
}

# Run main function
main "$@"
