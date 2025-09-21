# מדריך פריסה מהיר - Google Drive to GCS

## 🚀 אפשרות 1: פריסה ישירה (הכי מהיר - 2 דקות)

### דרישות:
- Google Cloud SDK מותקן
- התחברות לפרויקט: `gcloud auth login && gcloud config set project studio-beton`

### פקודות:
```bash
# חלץ את הקבצים
unzip gdrive_complete_ready.zip
cd gdrive_complete_package

# פרוס ישירות
gcloud run deploy gdrive-to-gcs-app \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

## 🔧 אפשרות 2: דרך GitHub (5 דקות)

### שלב 1: מחק שירות קיים
```bash
gcloud run services delete gdrive-to-gcs-app --region us-central1
```

### שלב 2: צור repository חדש
1. עבור ל-GitHub
2. צור repository חדש: `gdrive-gcs-transfer`
3. העלה את כל הקבצים מתוך `gdrive_complete_package`

### שלב 3: פרוס מ-GitHub
1. עבור ל-Cloud Run Console
2. Create Service > Deploy from repository
3. חבר את ה-repository החדש
4. Deploy

## 🐳 אפשרות 3: הרצה מקומית (לבדיקה)

```bash
cd gdrive_complete_package
pip install -r requirements.txt
python app.py
```

## 📋 פרטי OAuth שלך:
- Client ID: `850086889211-6pr0bo4ia90v54gd015uv9b6nqjmjf54.apps.googleusercontent.com`
- Client Secret: `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`
- Project ID: `studio-beton`

## ⚠️ חשוב:
לאחר הפריסה, עדכן את ה-OAuth redirect URI ל:
`https://YOUR-NEW-SERVICE-URL/oauth2callback`

## 🎯 הכל מוכן ונבדק!
הקוד עובד 100% - בחר אפשרות ופרוס!
