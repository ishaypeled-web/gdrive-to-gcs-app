# מדריך פריסה מהיר ל-Cloud Run

## ✅ **הקבצים מוכנים להעלאה:**

### **קבצים חיוניים לפריסה:**
- ✅ `Dockerfile` - הגדרות Container
- ✅ `requirements.txt` - תלויות Python
- ✅ `app.py` - אפליקציית Flask הראשית
- ✅ `templates/index.html` - דף הבית
- ✅ `templates/result.html` - דף תוצאות
- ✅ `cloudbuild.yaml` - הגדרות Cloud Build (אופציונלי)

### **קבצי תיעוד:**
- ✅ `README.md` - תיעוד מלא
- ✅ `DEPLOYMENT_GUIDE.md` - מדריך פריסה מפורט
- ✅ `deploy.sh` - סקריפט פריסה אוטומטי

## 🎯 **הגדרות Cloud Build שלך:**

### **Branch:** 
```
^main$
```

### **Build Type:** 
```
Dockerfile
```

### **Source location:** 
```
/Dockerfile
```

## 🚀 **שלבי הפריסה:**

1. **העלה את הקבצים ל-GitHub repository**
2. **חבר את ה-repository ל-Cloud Run**
3. **ודא שה-branch הוא `main`**
4. **לחץ "Save" בCloud Build**
5. **המתן לפריסה (כ-5-10 דקות)**

## 🔧 **לאחר הפריסה:**

1. **תקבל URL של השירות**
2. **עדכן OAuth redirect URI ל:**
   ```
   https://YOUR-SERVICE-URL/oauth2callback
   ```
3. **השירות יהיה זמין לשימוש!**

## 📋 **רשימת בדיקה:**
- [ ] כל הקבצים הועלו ל-GitHub
- [ ] Repository מחובר ל-Cloud Run
- [ ] Branch מוגדר ל-`main`
- [ ] Build Type מוגדר ל-`Dockerfile`
- [ ] Source location מוגדר ל-`/Dockerfile`
- [ ] OAuth redirect URI עודכן
