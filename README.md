# אפליקציית העברת קבצים מ-Google Drive ל-Google Cloud Storage

זוהי אפליקציית ווב מבוססת Flask המאפשרת למשתמשים להעביר קבצים ותיקיות מ-Google Drive לחשבון ה-Google Cloud Storage שלהם **ללא צורך בעריכת קוד או קבצי הגדרה**.

## תכונות מתקדמות

* **ממשק ווב מלא** - כל ההגדרות דרך הפרונטאנד
* **אימות OAuth 2.0 דינמי** - הכנסת פרטי OAuth ישירות בטופס
* **Service Account גמיש** - הדבקת JSON של Service Account בממשק
* **בדיקת חיבור** - אימות כל ההגדרות לפני ההעברה
* **דיווח מפורט** - תוצאות מפורטות עם אפשרות הורדת דוח
* **עיצוב מודרני** - ממשק רספונסיבי בעברית עם אנימציות

## הרצה מהירה

### 1. הורדה והתקנה
```bash
# הורד את הקבצים
unzip gdrive_to_gcs_app.zip
cd gdrive_to_gcs_app

# התקן תלויות
pip install -r requirements.txt

# הפעל את האפליקציה
python app.py
```

### 2. פתח בדפדפן
עבור אל: `http://localhost:8080`

### 3. הכן את הפרטים הנדרשים

#### OAuth Client ID
1. עבור אל [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. לחץ "Create Credentials" > "OAuth client ID"
3. בחר "Web application"
4. הוסף Redirect URI: `http://localhost:8080/oauth2callback`
5. העתק את Client ID ו-Client Secret

#### Service Account
1. עבור אל [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. צור Service Account חדש
3. הוסף תפקידים:
   - Storage Admin
   - Service Account User
4. צור מפתח JSON
5. העתק את כל תוכן קובץ ה-JSON

#### APIs נדרשים
הפעל את ה-APIs הבאים בפרויקט:
- Google Drive API
- Google Cloud Storage API

### 4. השתמש באפליקציה
1. מלא את כל השדות בטופס
2. לחץ "בדוק חיבור" לוודא שהכל תקין
3. לחץ "התחל העברה מלאה"
4. אשר את ההרשאות ב-Google
5. המתן לסיום ההעברה

## פריסה ב-Google Cloud Run

### פריסה אוטומטית
```bash
# הגדר פרויקט
gcloud config set project YOUR_PROJECT_ID

# הפעל APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# פרוס
gcloud run deploy gdrive-to-gcs-app \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

### עדכון Redirect URI
לאחר הפריסה, עדכן את ה-OAuth Client ID עם:
`https://YOUR-SERVICE-URL/oauth2callback`

## מבנה הפרויקט

```
gdrive_to_gcs_app/
├── app.py                  # באקאנד Flask מלא
├── templates/
│   ├── index.html         # טופס הגדרות מתקדם
│   └── result.html        # דף תוצאות מפורט
├── requirements.txt       # תלויות Python
├── Dockerfile            # לפריסה
├── cloudbuild.yaml       # Cloud Build
├── deploy.sh             # סקריפט פריסה
└── README.md             # קובץ זה
```

## שדות הטופס

| שדה | תיאור | דוגמה |
|-----|--------|--------|
| Client ID | מזהה OAuth Client | `123456789-abc.apps.googleusercontent.com` |
| Client Secret | סוד OAuth Client | `GOCSPX-xxxxxxxxxxxxxxxx` |
| Project ID (OAuth) | פרויקט OAuth | `my-oauth-project` |
| Drive Folder ID | מזהה תיקיית Drive | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |
| GCS Bucket | שם באקט | `my-storage-bucket` |
| GCS Project ID | פרויקט GCS | `my-gcs-project` |
| Service Account Key | JSON מלא | `{"type": "service_account", ...}` |

## תכונות מתקדמות

### בדיקת חיבור
לחצן "בדוק חיבור" מאמת:
- תקינות Service Account JSON
- גישה לבאקט GCS
- תקינות הגדרות OAuth

### דיווח מפורט
דף התוצאות כולל:
- סיכום סטטיסטי
- טבלת קבצים מפורטת
- אחוז הצלחה
- זמן העברה
- הורדת דוח CSV

### טיפול בשגיאות
- הודעות שגיאה ברורות בעברית
- דילוג על קבצי Google Docs
- המשך העברה גם במקרה של שגיאות בקבצים בודדים

## אבטחה

- כל הנתונים הרגישים נשמרים ב-session בלבד
- אין שמירה קבועה של credentials
- תקשורת מוצפנת (HTTPS בפרודקשן)
- אימות הרשאות לפני כל פעולה

## תמיכה

לבעיות או שאלות:
1. בדוק את הלוגים בקונסול הדפדפן
2. ודא שכל ה-APIs מופעלים
3. בדוק הרשאות Service Account
4. ודא שהבאקט קיים ונגיש

## רישיון

פרויקט זה זמין לשימוש חופשי ופתוח.
