import json

def update_arb(filepath, updates):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data.update(updates)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

en_updates = {
  "welcomeChooseOption": "How would you like to start?",
  "welcomeImNew": "First Time User",
  "@welcomeImNew": {
    "description": "Button for first-time registration"
  },
  "welcomeImNewSubtitle": "Set up your smart home for the first time",
  "welcomeHaveAccount": "I Already Have an Account",
  "welcomeHaveAccountSubtitle": "Sign in to your existing account"
}

ar_updates = {
  "welcomeChooseOption": "كيف تود أن تبدأ؟",
  "welcomeImNew": "مستخدم لأول مرة",
  "@welcomeImNew": {
    "description": "Button for first-time registration"
  },
  "welcomeImNewSubtitle": "إعداد منزلك الذكي لأول مرة",
  "welcomeHaveAccount": "لديّ حساب مسبقاً",
  "welcomeHaveAccountSubtitle": "تسجيل الدخول إلى حسابك الحالي"
}

update_arb('lib/l10n/app_en.arb', en_updates)
update_arb('lib/l10n/app_ar.arb', ar_updates)

print("Arb files updated successfully.")
