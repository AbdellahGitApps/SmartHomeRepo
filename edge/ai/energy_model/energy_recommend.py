def generate_energy_recommendations(analysis: dict) -> list[dict]:
    recs = []

    if analysis["weekly_trend"] == "up":
        recs.append({
            "type": "warning",
            "title": "ارتفاع الاستهلاك الأسبوعي",
            "message": "يوجد ارتفاع ملحوظ في استهلاك آخر أسبوع مقارنة بمتوسط آخر 4 أسابيع. يفضل مراجعة تشغيل الأجهزة الثقيلة مثل المكيفات والسخانات."
        })

    if analysis["expected_weekly_next_month_kwh"] > analysis["overall_weekly_avg_kwh"] * 1.15:
        recs.append({
            "type": "warning",
            "title": "توقع زيادة في الشهر القادم",
            "message": "من المتوقع أن يكون متوسط الاستهلاك الأسبوعي في الشهر القادم أعلى من المعدل العام. حاول تقليل تشغيل الأجهزة ذات الاستهلاك العالي لفترات طويلة."
        })

    if analysis["last_1_week_kwh"] > analysis["overall_weekly_avg_kwh"] * 1.20:
        recs.append({
            "type": "critical",
            "title": "استهلاك أعلى من المعتاد",
            "message": "استهلاك آخر أسبوع أعلى بكثير من المتوسط العام. افحص المكيفات والسخانات والأجهزة التي تعمل باستمرار."
        })

    if not recs:
        recs.append({
            "type": "info",
            "title": "الاستهلاك مستقر",
            "message": "لا توجد مؤشرات قوية على ارتفاع غير طبيعي في الاستهلاك. استمر في نمط الاستخدام الحالي مع متابعة دورية."
        })

    return recs