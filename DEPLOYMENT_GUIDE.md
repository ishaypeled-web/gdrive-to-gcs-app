# מדריך פריסה מפורט - אפליקציית העברת קבצים מ-Google Drive ל-GCS

## סקירה כללית

מדריך זה מספק הוראות שלב אחר שלב לפריסת אפליקציית ההעברה מ-Google Drive ל-Google Cloud Storage ב-Google Cloud Platform.

## שלב 1: הכנת הסביבה

### הגדרת פרויקט Google Cloud

1. **יצירת פרויקט חדש או בחירת פרויקט קיים:**
   ```bash
   gcloud projects create YOUR_PROJECT_ID
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **הפעלת APIs נדרשים:**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable drive.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

3. **הגדרת billing (חיוב):**
   - עבור אל [Google Cloud Console](https://console.cloud.google.com/billing)
   - קשר את הפרויקט לחשבון חיוב פעיל

## שלב 2: הגדרת OAuth 2.0

### יצירת OAuth Client ID

1. **עבור אל [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)**

2. **לחץ על "Create Credentials" > "OAuth client ID"**

3. **בחר "Web application" כסוג האפליקציה**

4. **הגדר Authorized redirect URIs:**
   - לפיתוח מקומי: `http://localhost:8080/oauth2callback`
   - לפריסה בענן: `https://YOUR_SERVICE_URL/oauth2callback`

5. **הורד את קובץ ה-JSON ושמור אותו בשם `client_secrets.json`**

### הגדרת OAuth Consent Screen

1. **עבור אל [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)**

2. **בחר "External" אם האפליקציה תהיה זמינה למשתמשים חיצוניים**

3. **מלא את הפרטים הנדרשים:**
   - שם האפליקציה
   - מייל תמיכה
   - לוגו (אופציונלי)

4. **הוסף scopes נדרשים:**
   - `https://www.googleapis.com/auth/drive.readonly`

## שלב 3: פריסה ב-Google Cloud Run

### שיטה 1: פריסה מקוד מקור (מומלץ)

```bash
# מתוך תיקיית הפרויקט
gcloud run deploy gdrive-to-gcs-app \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars CLIENT_SECRETS_FILE=client_secrets.json
```

### שיטה 2: פריסה עם Cloud Build

```bash
# העלאת הקוד ובנייה באמצעות Cloud Build
gcloud builds submit --config cloudbuild.yaml .
```

## שלב 4: הגדרת משתני סביבה

### הגדרת משתני סביבה ב-Cloud Run

```bash
gcloud run services update gdrive-to-gcs-app \
    --region us-central1 \
    --set-env-vars SECRET_KEY=your-secret-key-here \
    --set-env-vars CLIENT_SECRETS_FILE=client_secrets.json
```

### העלאת קובץ client_secrets.json

אפשרות 1 - שימוש ב-Secret Manager:
```bash
# יצירת secret
gcloud secrets create client-secrets --data-file=client_secrets.json

# הגדרת גישה לשירות
gcloud run services update gdrive-to-gcs-app \
    --region us-central1 \
    --set-env-vars CLIENT_SECRETS_FILE=/secrets/client_secrets.json
```

אפשרות 2 - הכללה בקוד (לא מומלץ לפרודקשן):
```bash
# העתקת הקובץ לתיקיית הפרויקט לפני הפריסה
cp /path/to/client_secrets.json ./client_secrets.json
```

## שלב 5: בדיקת הפריסה

### קבלת URL השירות

```bash
gcloud run services describe gdrive-to-gcs-app \
    --region us-central1 \
    --format 'value(status.url)'
```

### עדכון OAuth Redirect URIs

1. חזור להגדרות OAuth Client ID
2. הוסף את ה-URL החדש עם הסיומת `/oauth2callback`
3. שמור את השינויים

### בדיקת פונקציונליות

1. **גלוש לכתובת השירות**
2. **לחץ על "התחבר ל-Google Drive"**
3. **השלם את תהליך האימות**
4. **נסה להעביר קבצים מתיקייה ב-Drive לבאקט ב-GCS**

## שלב 6: ניטור ותחזוקה

### צפייה בלוגים

```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=gdrive-to-gcs-app" \
    --limit 50 \
    --format 'table(timestamp,textPayload)'
```

### עדכון השירות

```bash
# עדכון מקוד מקור
gcloud run deploy gdrive-to-gcs-app \
    --source . \
    --region us-central1
```

## פתרון בעיות נפוצות

### שגיאת "Invalid redirect URI"
- ודא שה-redirect URI מוגדר נכון ב-OAuth Client ID
- בדוק שאין רווחים או תווים מיותרים

### שגיאת "Access denied"
- ודא שהמשתמש אישר את ה-scopes הנדרשים
- בדוק שה-OAuth consent screen מוגדר נכון

### שגיאת "Bucket not found"
- ודא שהבאקט קיים בפרויקט הנכון
- בדוק שיש הרשאות גישה לבאקט

### שגיאות אימות Google Cloud
- ודא שה-service account של Cloud Run יש לו הרשאות מתאימות
- בדוק שמשתני הסביבה מוגדרים נכון

## אבטחה והמלצות

1. **השתמש ב-Secret Manager לאחסון credentials רגישים**
2. **הגדר HTTPS redirect URIs בלבד**
3. **הגבל את ה-scopes למינימום הנדרש**
4. **עקוב אחר לוגי הגישה והשימוש**
5. **עדכן באופן קבוע את התלויות והספריות**

## תמיכה נוספת

לתמיכה נוספת או דיווח על בעיות, עיין בתיעוד הרשמי של Google Cloud:
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
