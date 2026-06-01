#!/bin/bash
set -e

echo "=============================="
echo "  🎙️ Podcast Bot - نشر على GitHub"
echo "=============================="

# طلب اسم المستخدم من GitHub
read -p "اسم المستخدم فـ GitHub: " GITHUB_USER
read -p "اسم الـ Repository (مثلا: podcast-bot): " REPO_NAME
echo

# طلب Token (اختياري)
echo "🔑 باش ننشئو الـ repo أوتوماتيكياً، دير PAT (Personal Access Token)"
echo "  روح لـ: https://github.com/settings/tokens"
echo "  واختر: repo, workflow"
read -sp "GitHub Token (خلّي فاضي باش دير يدوياً): " GITHUB_TOKEN
echo

echo "------------------------------"
echo "1. تهيئة git..."
echo "------------------------------"
cd /home/abdo/ssabdo/tssf
git init
git checkout -b main

echo "------------------------------"
echo "2. إضافة الملفات..."
echo "------------------------------"
echo "*.mp4
__pycache__/
*.pyc
.DS_Store" > .gitignore

git add .
git commit -m "🎙️ Podcast Bot - تحميل + مونتاج + رفع لـ Facebook"

# إنشاء repo إذا كان الـ Token موجود
if [ -n "$GITHUB_TOKEN" ]; then
  echo "------------------------------"
  echo "3. إنشاء repo على GitHub..."
  echo "------------------------------"
  curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -X POST https://api.github.com/user/repos \
    -d "{\"name\":\"$REPO_NAME\", \"private\":false}" > /dev/null

  git remote add origin "https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git"
  git push -u origin main

  echo "------------------------------"
  echo "4. إضافة Secrets..."
  echo "------------------------------"
  echo "روح لـ: https://github.com/$GITHUB_USER/$REPO_NAME/settings/secrets/actions"
  echo " وزيد هاد الـ 4 Secrets:"
  echo
  echo "  CHANNEL_URL     = https://www.youtube.com/@samir-lail.mestapha-lherda"
  echo "  FB_PAGE_ID      = 1179824185206026"
  echo "  FB_ACCESS_TOKEN = <your-facebook-token>"
  echo "  GROQ_API_KEY    = <your-groq-api-key>"
  echo
  echo "------------------------------"
  echo "✅ تم! البوت غادي يجري كل يوم 6 مساءاً"
  echo "------------------------------"
  echo "  https://github.com/$GITHUB_USER/$REPO_NAME"
  echo "------------------------------"
else
  echo "------------------------------"
  echo "3. إنشاء الـ repo يدوياً..."
  echo "------------------------------"
  echo "  روح لـ: https://github.com/new"
  echo "  اسم الـ repo: $REPO_NAME"
  echo "  Public"
  echo "  لا تختار README"
  echo "  Create repository"
  echo
  echo "  من بعد شغّل:"
  echo "    git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git"
  echo "    git push -u origin main"
  echo
  echo "  من بعد زيد الـ Secrets فـ Settings → Secrets and variables → Actions:"
  echo "    CHANNEL_URL     = https://www.youtube.com/@samir-lail.mestapha-lherda"
  echo "    FB_PAGE_ID      = 1179824185206026"
  echo "    FB_ACCESS_TOKEN = TA3REF"
  echo "    GROQ_API_KEY    = <your-groq-api-key>"
  echo
  echo "✅ من بعد البوت غادي يجري كل يوم 6 مساءً"
fi
