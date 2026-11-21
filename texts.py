"""All user-facing strings, per language (en / ro / ru / uk)."""

# Per-language UI strings. Keys must exist in every language (en is the fallback).
TEXTS = {
    "en": {
        "choose_language": "🌍 <b>Welcome!</b>\nPlease choose your language:",
        "ask_allergies": (
            "✅ Language set to <b>English</b>.\n\n"
            "🤧 Do you have any skin allergies or ingredients you want to avoid?\n"
            "Type them separated by commas (e.g. <i>niacinamide, fragrance</i>) or type <b>None</b>."
        ),
        "ready": (
            "🎉 <b>All set!</b>\n"
            "🌐 Language: {language}\n"
            "🤧 Allergies: {allergies}\n\n"
            "📸 Send me a clear photo of a product's ingredient list (INCI) or paste the INCI text directly and I'll scan it."
        ),
        "no_allergies": "none",
        "no_modes": "none",
        "language_updated": "✅ Language updated: {language}",
        "allergies_updated": "✅ Allergies updated: {allergies}",
        "settings": (
            "⚙️ <b>Settings</b>\n"
            "🌐 Language: {language}\n"
            "🤧 Allergies: {allergies}\n"
            "🛡️ Safety modes: {modes}\n\n"
            "Tap a safety mode below to toggle it on/off:"
        ),
        "btn_language": "🌐 Change language",
        "btn_allergies": "🤧 Change allergies",
        "mode_pregnancy": "🤰 Pregnancy / Breastfeeding Safe",
        "mode_acne": "🫧 Acne-Prone (Comedogenic Check)",
        "mode_hair_clean": "🌿 Sulfate & Silicone Free",
        "help": (
            "ℹ️ <b>How to use</b>\n\n"
            "1️⃣ Send a clear photo of the ingredient list (INCI) <b>or paste the INCI text</b> from any online store.\n"
            "2️⃣ I check every ingredient against EU/Romanian regulations, your allergies, and your safety modes.\n"
            "3️⃣ You get a traffic light 🟢🟡🔴, a score out of 100, and a full breakdown.\n\n"
            "/start – restart setup\n/profile – profile, limits & referrals\n/compare – compare 2 products\n/history – scan history\n/buy – buy bonus scans\n/settings – language, allergies & safety modes"
        ),
        "too_long": "⚠️ That's too long. Please keep it under {n} characters.",
        "send_text": "✍️ Please type your allergies as text, or type <b>None</b>.",
        "cmd_start": "Start / Reset",
        "cmd_settings": "Language, allergies & safety modes",
        "cmd_help": "How to use",
        "cmd_profile": "Profile, limits & referrals",
        "cmd_history": "My scan history",
        "cmd_compare": "Compare 2 scanned products",
        "cmd_buy": "Buy non-expiring bonus scans",
        "processing": "⏳ Processing image and extracting ingredients...",
        "processing_text": "⏳ Analyzing pasted INCI ingredient list...",
        "error": "❌ An error occurred while analyzing. Please try again.",
        "limit_reached": (
            "⏳ You have used all your free scans for today ({n}/{n}) and have 0 bonus scans.\n"
            "Come back tomorrow for {n} new free scans, invite a friend for +5 bonus scans, or grab a bonus pack below! 💙"
        ),
        "not_a_list": "⚠️ <b>Could not read an ingredient list.</b>\n{reason}\n\nPlease send a clearer, well-lit photo.",
        "lbl_traffic": "Traffic-Light Score",
        "light_green": "Green (Safe)",
        "light_yellow": "Yellow (Caution)",
        "light_red": "Red (High Risk)",
        "lbl_score": "Safety Score",
        "lbl_verdict": "Verdict",
        "lbl_breakdown": "Detailed Breakdown",
        "no_details": "No ingredient details available.",
        "disclaimer": "Informational only - not medical advice.",
        "btn_scan": "📸 Scan Product",
        "btn_compare": "⚖️ Compare",
        "btn_profile": "👤 Profile & Limits",
        "btn_history": "🕘 My History",
        "btn_buy": "⭐ Buy Scans",
        "btn_menu_settings": "⚙️ Settings",
        "scan_intro": (
            "📸 <b>Scan a product (Photo or Text)</b>\n\n"
            "• <b>Photo:</b> Send a clear, well-lit photo of the product's <b>Ingredients / INCI</b> label.\n"
            "• <b>Online shopping:</b> Copy & paste the INCI ingredient list as text from <i>Farmacia Tei, Dr. Max, Notino, eMAG</i>, etc.\n\n"
            "💡 Tip: get close, avoid glare, or paste at least 2–3 ingredients separated by commas."
        ),
        "profile": (
            "👤 <b>Profile & Limits</b>\n\n"
            "🌐 Language: {language}\n"
            "🤧 Allergies: {allergies}\n"
            "🛡️ Safety modes: {modes}\n\n"
            "📸 Free scans today: <b>{scans}</b>\n"
            "⭐ Bonus scans (never expire): <b>{bonus}</b>\n"
            "🗂 Total scans: <b>{total}</b>\n\n"
            "🤝 <b>Referral Program</b>\n"
            "👥 Friends referred: <b>{referrals}</b>\n"
            "🔗 Your link: <code>{ref_link}</code>\n"
            "<i>Invite a friend → you both get <b>+5 bonus scans</b> after their first completed scan!</i>"
        ),
        "history_title": "🕘 <b>My History</b>\nYour latest scans — tap one to open its report:",
        "history_empty": "🕘 <b>No scans yet.</b>\nSend a photo of an ingredient list or paste an INCI list to get started!",
        "history_missing": "⚠️ This scan is no longer available.",
        "scan_untitled": "Scan",
        "unknown_product": "Unknown product",
        "lbl_alerts": "Personal & safety alerts",
        "lbl_irritants": "Flagged ingredients",
        "lbl_red": "High-risk ingredients",
        "lbl_yellow": "Caution ingredients",
        "lbl_safe": "Safe ingredients",
        "lbl_alternatives": "Pharmacy alternatives",
        "no_ingredients_found": (
            "⚠️ <b>No ingredient list found in this photo.</b>\n\n"
            "I never guess ingredients from the brand or front of the package.\n"
            "📸 Please photograph the <b>\"Ingredients\" / INCI</b> section on the back of the label clearly and send it again."
        ),
        "no_ingredients_text": (
            "⚠️ <b>No cosmetic ingredient list (INCI) detected in your message.</b>\n\n"
            "Your scan was not deducted. Please paste an actual INCI ingredient list (e.g. <i>Aqua, Glycerin, Niacinamide, Parfum...</i>) or send a clear photo of the label."
        ),
        "rule_formaldehyde": "Formaldehyde releaser (strong allergen / sensitizer).",
        "rule_banned": "Restricted or high-risk substance under EU regulations.",
        "rule_uv_filter": "Controversial chemical UV filter (potential endocrine / irritation concern).",
        "rule_fragrance": "Fragrance / declarable allergen (potential skin sensitizer).",
        "rule_sulfate": "Harsh sulfate surfactant (can strip and irritate skin).",
        "rule_alcohol": "Drying alcohol (can irritate or dehydrate skin).",
        "rule_peg_paraben": "PEG / paraben compound (moderate regulatory / sensitivity concern).",
        "rule_peg": "PEG emulsifier (potential penetration enhancer / impurity concern).",
        "rule_paraben": "Paraben preservative (moderate regulatory / sensitivity concern).",
        "rule_bht_bha": "Synthetic antioxidant (BHT/BHA — potential endocrine disruptor).",
        "rule_aluminum": "Antiperspirant aluminum salt (caution for sensitive skin).",
        "rule_microplastic": "Synthetic microplastic polymer.",
        "rule_petrochemical": "Occlusive petrochemical emollient.",
        "rule_allergy": "Matches your declared personal allergy.",
        "rule_pregnancy": "Not recommended during pregnancy / breastfeeding.",
        "rule_comedogenic": "Comedogenic ingredient (may clog pores on acne-prone skin).",
        "rule_sulfate_silicone": "Sulfate / non-soluble silicone (flagged by your hair mode).",
        "report_title": "Ingredient Analysis",
        "btn_ask": "💬 Ask about this product",
        "btn_alternatives": "💊 Suggest alternatives",
        "btn_cancel": "❌ Cancel",
        "qa_prompt": (
            "💬 <b>Ask about this product</b>\n\n"
            "Type any question about this ingredient list (e.g. suitability for sensitive skin, pregnancy, acne, or how an ingredient works).\n"
            "Tap <b>Cancel</b> when you're done."
        ),
        "qa_cancelled": "✅ Exited product Q&A.",
        "qa_send_text": "✍️ Please type your question as text, or tap <b>Cancel</b>.",
        "qa_error": "❌ Could not answer your question right now. Please try again.",
        "alt_loading": "💊 Finding Romanian pharmacy alternatives...",
        "alt_empty": "ℹ️ Could not find specific pharmacy alternatives for this formula.",
        "alt_error": "❌ Could not fetch alternatives right now. Please try again.",
        "cmp_need_two": "⚖️ <b>Not enough scans to compare.</b>\nYou need at least <b>2 completed scans</b> in your history. Scan a couple of products first!",
        "cmp_pick1": "⚖️ <b>Compare 2 Products — Step 1/2</b>\nSelect <b>Product #1</b> from your recent scans:",
        "cmp_pick2": "⚖️ <b>Compare 2 Products — Step 2/2</b>\nProduct #1: <b>{p1}</b>\nNow select <b>Product #2</b>:",
        "cmp_loading": "⚖️ Comparing products...",
        "cmp_cancelled": "✅ Comparison cancelled.",
        "cmp_title": "⚖️ <b>Product Comparison</b>",
        "cmp_p1": "Product #1",
        "cmp_p2": "Product #2",
        "cmp_winner": "🏆 <b>Winner:</b>",
        "cmp_tie": "🤝 <b>Tie</b>",
        "cmp_diffs": "🔍 <b>Key Differences:</b>",
        "cmp_verdict": "📝 <b>Final Verdict:</b>",
        "cmp_error": "❌ Could not compare the products right now. Please try again.",
        "buy_menu": (
            "⭐ <b>Buy Bonus Scans</b>\n\n"
            "Bonus scans <b>never expire</b> at midnight and are used automatically after your 3 daily free scans.\n\n"
            "Choose a package below (paid with Telegram Stars):"
        ),
        "btn_pack_10": "⭐ 10 Bonus Scans — 25 Stars",
        "btn_pack_30": "🌟 30 Bonus Scans — 60 Stars",
        "inv_title_10": "10 Bonus Scans",
        "inv_desc_10": "10 non-expiring bonus ingredient scans (photo or INCI text).",
        "inv_title_30": "30 Bonus Scans",
        "inv_desc_30": "30 non-expiring bonus ingredient scans (photo or INCI text).",
        "pay_success": "🎉 <b>Payment successful!</b>\nAdded <b>+{added} bonus scans</b>.\n⭐ New bonus balance: <b>{balance}</b>",
        "pay_duplicate": "ℹ️ This payment was already credited to your balance.",
        "ref_reward_referee": "🎁 <b>Referral bonus!</b> You completed your first scan and received <b>+{n} bonus scans</b>!",
        "ref_reward_referrer": "🎉 <b>Referral reward!</b> Your invited friend completed their first scan — you received <b>+{n} bonus scans</b>!",
        "bonus_gift_notify": "🎁 <b>You received +{amount} bonus scans!</b>\n⭐ New bonus balance: <b>{balance}</b>",
    },
    "ro": {
        "choose_language": "🌍 <b>Bun venit!</b>\nAlege limba ta:",
        "ask_allergies": (
            "✅ Limba setată: <b>Română</b>.\n\n"
            "🤧 Ai alergii cutanate sau ingrediente pe care vrei să le eviți?\n"
            "Scrie-le separate prin virgulă (ex. <i>niacinamide, fragrance</i>) sau scrie <b>Nu</b>."
        ),
        "ready": (
            "🎉 <b>Totul este gata!</b>\n"
            "🌐 Limba: {language}\n"
            "🤧 Alergii: {allergies}\n\n"
            "📸 Trimite-mi o fotografie clară a listei de ingrediente (INCI) sau lipește textul INCI direct și îl voi scana."
        ),
        "no_allergies": "niciuna",
        "no_modes": "niciunul",
        "language_updated": "✅ Limba a fost actualizată: {language}",
        "allergies_updated": "✅ Alergiile au fost actualizate: {allergies}",
        "settings": (
            "⚙️ <b>Setări</b>\n"
            "🌐 Limba: {language}\n"
            "🤧 Alergii: {allergies}\n"
            "🛡️ Moduri de siguranță: {modes}\n\n"
            "Atinge un mod de mai jos pentru a-l activa/dezactiva:"
        ),
        "btn_language": "🌐 Schimbă limba",
        "btn_allergies": "🤧 Schimbă alergiile",
        "mode_pregnancy": "🤰 Sigur în sarcină / alăptare",
        "mode_acne": "🫧 Ten acneic (Verificare comedogenică)",
        "mode_hair_clean": "🌿 Fără sulfați și siliconi",
        "help": (
            "ℹ️ <b>Cum se folosește</b>\n\n"
            "1️⃣ Trimite o fotografie clară a listei de ingrediente (INCI) <b>sau lipește textul INCI</b> de pe orice magazin online.\n"
            "2️⃣ Verific fiecare ingredient conform reglementărilor UE/României, alergiilor și modurilor tale de siguranță.\n"
            "3️⃣ Primești un semafor 🟢🟡🔴, un scor din 100 și o analiză completă.\n\n"
            "/start – reia configurarea\n/profile – profil, limite și recomandări\n/compare – compară 2 produse\n/history – istoric scanări\n/buy – cumpără scanări bonus\n/settings – limbă, alergii și moduri"
        ),
        "too_long": "⚠️ Textul este prea lung. Maximum {n} de caractere.",
        "send_text": "✍️ Scrie alergiile ca text sau scrie <b>Nu</b>.",
        "cmd_start": "Start / Resetare",
        "cmd_settings": "Limbă, alergii și moduri de siguranță",
        "cmd_help": "Cum se folosește",
        "cmd_profile": "Profil, limite și recomandări",
        "cmd_history": "Istoricul scanărilor",
        "cmd_compare": "Compară 2 produse scanate",
        "cmd_buy": "Cumpără scanări bonus fără expirare",
        "processing": "⏳ Se procesează imaginea și se extrag ingredientele...",
        "processing_text": "⏳ Se analizează lista de ingrediente (INCI)...",
        "error": "❌ A apărut o eroare la analiză. Te rugăm să încerci din nou.",
        "limit_reached": (
            "⏳ Ai folosit toate scanările gratuite de azi ({n}/{n}) și ai 0 scanări bonus.\n"
            "Revino mâine pentru {n} scanări gratuite noi, invită un prieten pentru +5 scanări bonus sau alege un pachet mai jos! 💙"
        ),
        "not_a_list": "⚠️ <b>Nu am putut citi lista de ingrediente.</b>\n{reason}\n\nTe rugăm să trimiți o fotografie mai clară și bine luminată.",
        "lbl_traffic": "Scor semafor",
        "light_green": "Verde (Sigur)",
        "light_yellow": "Galben (Precauție)",
        "light_red": "Roșu (Risc ridicat)",
        "lbl_score": "Scor de siguranță",
        "lbl_verdict": "Verdict",
        "lbl_breakdown": "Analiză detaliată",
        "no_details": "Nu sunt disponibile detalii despre ingrediente.",
        "disclaimer": "Doar cu titlu informativ - nu reprezintă sfat medical.",
        "btn_scan": "📸 Scanează produs",
        "btn_compare": "⚖️ Compară",
        "btn_profile": "👤 Profil și limite",
        "btn_history": "🕘 Istoricul meu",
        "btn_buy": "⭐ Cumpără scanări",
        "btn_menu_settings": "⚙️ Setări",
        "scan_intro": (
            "📸 <b>Scanează un produs (Foto sau Text)</b>\n\n"
            "• <b>Foto:</b> Trimite o fotografie clară a secțiunii <b>Ingredients / INCI</b> de pe etichetă.\n"
            "• <b>Cumpărături online:</b> Copiază și lipește lista de ingrediente (INCI) ca text de pe <i>Farmacia Tei, Dr. Max, Notino, eMAG</i> etc.\n\n"
            "💡 Sfat: apropie-te, evită reflexiile sau lipește cel puțin 2–3 ingrediente separate prin virgulă."
        ),
        "profile": (
            "👤 <b>Profil și limite</b>\n\n"
            "🌐 Limba: {language}\n"
            "🤧 Alergii: {allergies}\n"
            "🛡️ Moduri de siguranță: {modes}\n\n"
            "📸 Scanări gratuite azi: <b>{scans}</b>\n"
            "⭐ Scanări bonus (nu expiră): <b>{bonus}</b>\n"
            "🗂 Total scanări: <b>{total}</b>\n\n"
            "🤝 <b>Program de recomandare</b>\n"
            "👥 Prieteni invitați: <b>{referrals}</b>\n"
            "🔗 Linkul tău: <code>{ref_link}</code>\n"
            "<i>Invită un prieten → primiți amândoi <b>+5 scanări bonus</b> după prima lui scanare finalizată!</i>"
        ),
        "history_title": "🕘 <b>Istoricul meu</b>\nUltimele scanări — atinge una pentru a deschide raportul:",
        "history_empty": "🕘 <b>Nicio scanare încă.</b>\nTrimite o fotografie cu lista de ingrediente sau lipește textul INCI ca să începi!",
        "history_missing": "⚠️ Această scanare nu mai este disponibilă.",
        "scan_untitled": "Scanare",
        "unknown_product": "Produs necunoscut",
        "lbl_alerts": "Alerte personale și de siguranță",
        "lbl_irritants": "Ingrediente semnalate",
        "lbl_red": "Ingrediente cu risc ridicat",
        "lbl_yellow": "Ingrediente cu precauție",
        "lbl_safe": "Ingrediente sigure",
        "lbl_alternatives": "Alternative din farmacie",
        "no_ingredients_found": (
            "⚠️ <b>Nu am găsit lista de ingrediente în această fotografie.</b>\n\n"
            "Nu ghicesc niciodată ingredientele după brand sau fața ambalajului.\n"
            "📸 Te rog să fotografiezi clar secțiunea <b>„Ingredients” / INCI</b> de pe spatele etichetei și să o trimiți din nou."
        ),
        "no_ingredients_text": (
            "⚠️ <b>Nu am detectat o listă de ingrediente cosmetice (INCI) în mesajul tău.</b>\n\n"
            "Scanarea nu a fost scăzută. Te rog să lipești o listă reală de ingrediente INCI (ex. <i>Aqua, Glycerin, Niacinamide, Parfum...</i>) sau să trimiți o fotografie clară a etichetei."
        ),
        "rule_formaldehyde": "Eliberator de formaldehidă (alergen / sensibilizant puternic).",
        "rule_banned": "Substanță restricționată sau cu risc ridicat conform reglementărilor UE.",
        "rule_uv_filter": "Filtru UV chimic controversat (potențial perturbator endocrin / iritant).",
        "rule_fragrance": "Parfum / alergen declarabil (potențial sensibilizant cutanat).",
        "rule_sulfate": "Sulfat agresiv (poate usca și irita pielea).",
        "rule_alcohol": "Alcool cu efect de uscare (poate irita sau deshidrata pielea).",
        "rule_peg_paraben": "Compus PEG / paraben (preocupare moderată de sensibilitate / reglementare).",
        "rule_peg": "Emulgator PEG (poate crește permeabilitatea pielii / risc de impurități).",
        "rule_paraben": "Conservant paraben (preocupare moderată de sensibilitate / reglementare).",
        "rule_bht_bha": "Antioxidant sintetic (BHT/BHA — potențial perturbator endocrin).",
        "rule_aluminum": "Sare de aluminiu antiperspirantă (precauție pentru pielea sensibilă).",
        "rule_microplastic": "Polimer microplastic sintetic.",
        "rule_petrochemical": "Emolient petrochimic ocluziv.",
        "rule_allergy": "Corespunde alergiei tale personale declarate.",
        "rule_pregnancy": "Nerecomandat în timpul sarcinii / alăptării.",
        "rule_comedogenic": "Ingredient comedogenic (poate bloca porii tenului acneic).",
        "rule_sulfate_silicone": "Sulfat / silicon insolubil (semnalat de modul tău pentru păr).",
        "report_title": "Analiza ingredientelor",
        "btn_ask": "💬 Întreabă despre produs",
        "btn_alternatives": "💊 Sugerează alternative",
        "btn_cancel": "❌ Anulează",
        "qa_prompt": (
            "💬 <b>Întreabă despre acest produs</b>\n\n"
            "Scrie orice întrebare despre această listă de ingrediente (ex. potrivire pentru ten sensibil, sarcină, acnee sau rolul unui ingredient).\n"
            "Apasă <b>Anulează</b> când termini."
        ),
        "qa_cancelled": "✅ Ai ieșit din modul de întrebări.",
        "qa_send_text": "✍️ Te rog să scrii întrebarea ca text sau să apeși <b>Anulează</b>.",
        "qa_error": "❌ Nu am putut răspunde acum. Te rog să încerci din nou.",
        "alt_loading": "💊 Caut alternative din farmaciile din România...",
        "alt_empty": "ℹ️ Nu am putut găsi alternative specifice din farmacie pentru această formulă.",
        "alt_error": "❌ Nu am putut genera alternative acum. Te rog să încerci din nou.",
        "cmp_need_two": "⚖️ <b>Prea puține scanări pentru comparare.</b>\nAi nevoie de cel puțin <b>2 scanări finalizate</b> în istoric. Scanează mai întâi două produse!",
        "cmp_pick1": "⚖️ <b>Compară 2 produse — Pasul 1/2</b>\nAlege <b>Produsul #1</b> din scanările recente:",
        "cmp_pick2": "⚖️ <b>Compară 2 produse — Pasul 2/2</b>\nProdusul #1: <b>{p1}</b>\nAcum alege <b>Produsul #2</b>:",
        "cmp_loading": "⚖️ Se compară produsele...",
        "cmp_cancelled": "✅ Compararea a fost anulată.",
        "cmp_title": "⚖️ <b>Comparație produse</b>",
        "cmp_p1": "Produsul #1",
        "cmp_p2": "Produsul #2",
        "cmp_winner": "🏆 <b>Câștigător:</b>",
        "cmp_tie": "🤝 <b>Egalitate</b>",
        "cmp_diffs": "🔍 <b>Diferențe cheie:</b>",
        "cmp_verdict": "📝 <b>Verdict final:</b>",
        "cmp_error": "❌ Nu am putut compara produsele acum. Te rog să încerci din nou.",
        "buy_menu": (
            "⭐ <b>Cumpără scanări bonus</b>\n\n"
            "Scanările bonus <b>nu expiră niciodată</b> la miezul nopții și se folosesc automat după cele 3 scanări gratuite zilnice.\n\n"
            "Alege un pachet mai jos (plată cu Telegram Stars):"
        ),
        "btn_pack_10": "⭐ 10 Scanări bonus — 25 Stars",
        "btn_pack_30": "🌟 30 Scanări bonus — 60 Stars",
        "inv_title_10": "10 Scanări bonus",
        "inv_desc_10": "10 scanări bonus fără expirare (foto sau text INCI).",
        "inv_title_30": "30 Scanări bonus",
        "inv_desc_30": "30 scanări bonus fără expirare (foto sau text INCI).",
        "pay_success": "🎉 <b>Plată reușită!</b>\nS-au adăugat <b>+{added} scanări bonus</b>.\n⭐ Sold nou bonus: <b>{balance}</b>",
        "pay_duplicate": "ℹ️ Această plată a fost deja adăugată în soldul tău.",
        "ref_reward_referee": "🎁 <b>Bonus de recomandare!</b> Ai finalizat prima scanare și ai primit <b>+{n} scanări bonus</b>!",
        "ref_reward_referrer": "🎉 <b>Recompensă de recomandare!</b> Prietenul invitat a finalizat prima scanare — ai primit <b>+{n} scanări bonus</b>!",
        "bonus_gift_notify": "🎁 <b>Ai primit +{amount} scanări bonus!</b>\n⭐ Sold nou bonus: <b>{balance}</b>",
    },
    "ru": {
        "choose_language": "🌍 <b>Добро пожаловать!</b>\nВыберите язык:",
        "ask_allergies": (
            "✅ Язык установлен: <b>Русский</b>.\n\n"
            "🤧 Есть ли у вас аллергия кожи или ингредиенты, которых нужно избегать?\n"
            "Напишите через запятую (например, <i>niacinamide, fragrance</i>) или напишите <b>Нет</b>."
        ),
        "ready": (
            "🎉 <b>Всё готово!</b>\n"
            "🌐 Язык: {language}\n"
            "🤧 Аллергии: {allergies}\n\n"
            "📸 Отправьте чёткое фото состава (INCI) или вставьте текст INCI напрямую, и я его проверю."
        ),
        "no_allergies": "нет",
        "no_modes": "нет",
        "language_updated": "✅ Язык обновлён: {language}",
        "allergies_updated": "✅ Аллергии обновлены: {allergies}",
        "settings": (
            "⚙️ <b>Настройки</b>\n"
            "🌐 Язык: {language}\n"
            "🤧 Аллергии: {allergies}\n"
            "🛡️ Режимы безопасности: {modes}\n\n"
            "Нажмите на режим ниже, чтобы включить или выключить его:"
        ),
        "btn_language": "🌐 Сменить язык",
        "btn_allergies": "🤧 Изменить аллергии",
        "mode_pregnancy": "🤰 Безопасно при беременности / ГВ",
        "mode_acne": "🫧 Склонность к акне (Комедогенность)",
        "mode_hair_clean": "🌿 Без сульфатов и силиконов",
        "help": (
            "ℹ️ <b>Как пользоваться</b>\n\n"
            "1️⃣ Отправьте чёткое фото состава (INCI) <b>или вставьте текст состава</b> из любого интернет-магазина.\n"
            "2️⃣ Я проверяю каждый ингредиент по нормам ЕС/Румынии, вашим аллергиям и режимам безопасности.\n"
            "3️⃣ Вы получите светофор 🟢🟡🔴, оценку из 100 и полный разбор.\n\n"
            "/start – начать заново\n/profile – профиль, лимиты и рефералы\n/compare – сравнить 2 продукта\n/history – история\n/buy – купить бонусные сканы\n/settings – язык, аллергии и режимы"
        ),
        "too_long": "⚠️ Слишком длинно. Максимум {n} символов.",
        "send_text": "✍️ Напишите аллергии текстом или напишите <b>Нет</b>.",
        "cmd_start": "Начать / Сброс",
        "cmd_settings": "Язык, аллергии и режимы безопасности",
        "cmd_help": "Как пользоваться",
        "cmd_profile": "Профиль, лимиты и рефералы",
        "cmd_history": "История сканирований",
        "cmd_compare": "Сравнить 2 отсканированных продукта",
        "cmd_buy": "Купить несгораемые бонусные сканы",
        "processing": "⏳ Обрабатываю изображение и извлекаю состав...",
        "processing_text": "⏳ Анализирую вставленный список ингредиентов (INCI)...",
        "error": "❌ Произошла ошибка при анализе. Пожалуйста, попробуйте ещё раз.",
        "limit_reached": (
            "⏳ Вы использовали все бесплатные сканирования на сегодня ({n}/{n}), а бонусных сканов — 0.\n"
            "Возвращайтесь завтра за {n} новыми бесплатными сканами, пригласите друга за +5 бонусных сканов или выберите пакет ниже! 💙"
        ),
        "not_a_list": "⚠️ <b>Не удалось прочитать список ингредиентов.</b>\n{reason}\n\nПожалуйста, отправьте более чёткое, хорошо освещённое фото.",
        "lbl_traffic": "Оценка светофора",
        "light_green": "Зелёный (Безопасно)",
        "light_yellow": "Жёлтый (Осторожно)",
        "light_red": "Красный (Высокий риск)",
        "lbl_score": "Оценка безопасности",
        "lbl_verdict": "Вердикт",
        "lbl_breakdown": "Подробный разбор",
        "no_details": "Подробности об ингредиентах недоступны.",
        "disclaimer": "Только для информации - не является медицинской рекомендацией.",
        "btn_scan": "📸 Сканировать продукт",
        "btn_compare": "⚖️ Сравнить",
        "btn_profile": "👤 Профиль и лимиты",
        "btn_history": "🕘 Моя история",
        "btn_buy": "⭐ Купить сканы",
        "btn_menu_settings": "⚙️ Настройки",
        "scan_intro": (
            "📸 <b>Сканирование продукта (Фото или Текст)</b>\n\n"
            "• <b>Фото:</b> Отправьте чёткое фото раздела <b>Ingredients / INCI</b> на этикетке.\n"
            "• <b>Онлайн-покупки:</b> Скопируйте и вставьте список ингредиентов (INCI) текстом с <i>Farmacia Tei, Dr. Max, Notino, eMAG</i> и др.\n\n"
            "💡 Совет: избегайте бликов на фото или вставьте минимум 2–3 ингредиента через запятую."
        ),
        "profile": (
            "👤 <b>Профиль и лимиты</b>\n\n"
            "🌐 Язык: {language}\n"
            "🤧 Аллергии: {allergies}\n"
            "🛡️ Режимы безопасности: {modes}\n\n"
            "📸 Бесплатных сканов сегодня: <b>{scans}</b>\n"
            "⭐ Бонусных сканов (не сгорают): <b>{bonus}</b>\n"
            "🗂 Всего сканирований: <b>{total}</b>\n\n"
            "🤝 <b>Реферальная программа</b>\n"
            "👥 Приглашено друзей: <b>{referrals}</b>\n"
            "🔗 Ваша ссылка: <code>{ref_link}</code>\n"
            "<i>Пригласите друга → вы оба получите <b>+5 бонусных сканов</b> после его первого сканирования!</i>"
        ),
        "history_title": "🕘 <b>Моя история</b>\nПоследние сканирования — нажмите, чтобы открыть отчёт:",
        "history_empty": "🕘 <b>Сканирований пока нет.</b>\nОтправьте фото состава или вставьте список INCI, чтобы начать!",
        "history_missing": "⚠️ Это сканирование больше недоступно.",
        "scan_untitled": "Скан",
        "unknown_product": "Неизвестный продукт",
        "lbl_alerts": "Личные и профильные предупреждения",
        "lbl_irritants": "Отмеченные ингредиенты",
        "lbl_red": "Ингредиенты высокого риска",
        "lbl_yellow": "Ингредиенты с осторожностью",
        "lbl_safe": "Безопасные ингредиенты",
        "lbl_alternatives": "Аптечные альтернативы",
        "no_ingredients_found": (
            "⚠️ <b>На этом фото не найден список ингредиентов.</b>\n\n"
            "Я никогда не угадываю состав по бренду или лицевой стороне упаковки.\n"
            "📸 Пожалуйста, чётко сфотографируйте раздел <b>«Ingredients» / INCI</b> на обратной стороне этикетки и отправьте снова."
        ),
        "no_ingredients_text": (
            "⚠️ <b>В вашем сообщении не обнаружен список косметических ингредиентов (INCI).</b>\n\n"
            "Скан не был списан. Пожалуйста, вставьте реальный состав INCI (например, <i>Aqua, Glycerin, Niacinamide, Parfum...</i>) или отправьте чёткое фото этикетки."
        ),
        "rule_formaldehyde": "Донор формальдегида (сильный аллерген / сенсибилизатор).",
        "rule_banned": "Ограниченное или высокорискованное вещество по нормам ЕС.",
        "rule_uv_filter": "Спорный химический УФ-фильтр (потенциальный эндокринный / раздражающий риск).",
        "rule_fragrance": "Отдушка / декларируемый аллерген (возможная сенсибилизация кожи).",
        "rule_sulfate": "Агрессивный сульфат (может пересушивать и раздражать кожу).",
        "rule_alcohol": "Подсушивающий спирт (может вызывать раздражение и сухость).",
        "rule_peg_paraben": "ПЭГ / парабен (умеренный риск раздражения или регуляторные ограничения).",
        "rule_peg": "Эмульгатор ПЭГ (может повышать проницаемость кожи / риск примесей).",
        "rule_paraben": "Консервант парабен (умеренный риск раздражения или регуляторные ограничения).",
        "rule_bht_bha": "Синтетический антиоксидант (BHT/BHA — потенциальный эндокринный дизраптор).",
        "rule_aluminum": "Соль алюминия в антиперспирантах (осторожно при чувствительной коже).",
        "rule_microplastic": "Синтетический микропластик.",
        "rule_petrochemical": "Окклюзивный нефтехимический компонент.",
        "rule_allergy": "Совпадает с вашей личной аллергией.",
        "rule_pregnancy": "Не рекомендуется при беременности и грудном вскармливании.",
        "rule_comedogenic": "Комедогенный компонент (может забивать поры при склонности к акне).",
        "rule_sulfate_silicone": "Сульфат / нерастворимый силикон (отмечен вашим режимом для волос).",
        "report_title": "Анализ состава",
        "btn_ask": "💬 Спросить о продукте",
        "btn_alternatives": "💊 Подобрать альтернативы",
        "btn_cancel": "❌ Отмена",
        "qa_prompt": (
            "💬 <b>Задайте вопрос об этом продукте</b>\n\n"
            "Напишите любой вопрос по этому составу (например, подходит ли для чувствительной кожи, при беременности, акне или зачем нужен конкретный ингредиент).\n"
            "Нажмите <b>Отмена</b>, когда закончите."
        ),
        "qa_cancelled": "✅ Режим вопросов закрыт.",
        "qa_send_text": "✍️ Пожалуйста, напишите вопрос текстом или нажмите <b>Отмена</b>.",
        "qa_error": "❌ Не удалось ответить на вопрос. Пожалуйста, попробуйте ещё раз.",
        "alt_loading": "💊 Подбираю альтернативы из аптек Румынии...",
        "alt_empty": "ℹ️ Не удалось подобрать конкретные аптечные альтернативы для этой формулы.",
        "alt_error": "❌ Не удалось подобрать альтернативы сейчас. Пожалуйста, попробуйте ещё раз.",
        "cmp_need_two": "⚖️ <b>Недостаточно сканирований для сравнения.</b>\nВ истории должно быть минимум <b>2 завершённых скана</b>. Сначала отсканируйте два продукта!",
        "cmp_pick1": "⚖️ <b>Сравнение 2 продуктов — Шаг 1/2</b>\nВыберите <b>Продукт №1</b> из недавних сканирований:",
        "cmp_pick2": "⚖️ <b>Сравнение 2 продуктов — Шаг 2/2</b>\nПродукт №1: <b>{p1}</b>\nТеперь выберите <b>Продукт №2</b>:",
        "cmp_loading": "⚖️ Сравниваю продукты...",
        "cmp_cancelled": "✅ Сравнение отменено.",
        "cmp_title": "⚖️ <b>Сравнение продуктов</b>",
        "cmp_p1": "Продукт №1",
        "cmp_p2": "Продукт №2",
        "cmp_winner": "🏆 <b>Победитель:</b>",
        "cmp_tie": "🤝 <b>Ничья</b>",
        "cmp_diffs": "🔍 <b>Ключевые отличия:</b>",
        "cmp_verdict": "📝 <b>Итоговый вердикт:</b>",
        "cmp_error": "❌ Не удалось сравнить продукты сейчас. Пожалуйста, попробуйте ещё раз.",
        "buy_menu": (
            "⭐ <b>Купить бонусные сканы</b>\n\n"
            "Бонусные сканы <b>никогда не сгорают</b> в полночь и расходуются автоматически после 3 ежедневных бесплатных сканов.\n\n"
            "Выберите пакет ниже (оплата через Telegram Stars):"
        ),
        "btn_pack_10": "⭐ 10 бонусных сканов — 25 Stars",
        "btn_pack_30": "🌟 30 бонусных сканов — 60 Stars",
        "inv_title_10": "10 бонусных сканов",
        "inv_desc_10": "10 несгораемых бонусных сканирований состава (по фото или тексту INCI).",
        "inv_title_30": "30 бонусных сканов",
        "inv_desc_30": "30 несгораемых бонусных сканирований состава (по фото или тексту INCI).",
        "pay_success": "🎉 <b>Оплата прошла успешно!</b>\nНачислено <b>+{added} бонусных сканов</b>.\n⭐ Новый бонусный баланс: <b>{balance}</b>",
        "pay_duplicate": "ℹ️ Этот платёж уже был зачислен на ваш баланс.",
        "ref_reward_referee": "🎁 <b>Реферальный бонус!</b> Вы выполнили первое сканирование и получили <b>+{n} бонусных сканов</b>!",
        "ref_reward_referrer": "🎉 <b>Реферальная награда!</b> Приглашённый друг выполнил первое сканирование — вам начислено <b>+{n} бонусных сканов</b>!",
        "bonus_gift_notify": "🎁 <b>Вам начислено +{amount} бонусных сканов!</b>\n⭐ Новый бонусный баланс: <b>{balance}</b>",
    },
    "uk": {
        "choose_language": "🌍 <b>Ласкаво просимо!</b>\nОберіть мову:",
        "ask_allergies": (
            "✅ Мову встановлено: <b>Українська</b>.\n\n"
            "🤧 Чи є у вас алергія шкіри або інгредієнти, яких слід уникати?\n"
            "Напишіть через кому (наприклад, <i>niacinamide, fragrance</i>) або напишіть <b>Ні</b>."
        ),
        "ready": (
            "🎉 <b>Все готово!</b>\n"
            "🌐 Мова: {language}\n"
            "🤧 Алергії: {allergies}\n\n"
            "📸 Надішліть чітке фото складу (INCI) або вставте текст INCI напряму, і я його перевірю."
        ),
        "no_allergies": "немає",
        "no_modes": "немає",
        "language_updated": "✅ Мову оновлено: {language}",
        "allergies_updated": "✅ Алергії оновлено: {allergies}",
        "settings": (
            "⚙️ <b>Налаштування</b>\n"
            "🌐 Мова: {language}\n"
            "🤧 Алергії: {allergies}\n"
            "🛡️ Режими безпеки: {modes}\n\n"
            "Натисніть на режим нижче, щоб увімкнути або вимкнути його:"
        ),
        "btn_language": "🌐 Змінити мову",
        "btn_allergies": "🤧 Змінити алергії",
        "mode_pregnancy": "🤰 Безпечно при вагітності / ГВ",
        "mode_acne": "🫧 Схильність до акне (Комедогенність)",
        "mode_hair_clean": "🌿 Без сульфатів і силіконів",
        "help": (
            "ℹ️ <b>Як користуватися</b>\n\n"
            "1️⃣ Надішліть чітке фото складу (INCI) <b>або вставте текст складу</b> з будь-якого інтернет-магазину.\n"
            "2️⃣ Я перевіряю кожен інгредієнт за нормами ЄС/Румунії, вашими алергіями та режимами безпеки.\n"
            "3️⃣ Ви отримаєте світлофор 🟢🟡🔴, оцінку зі 100 та повний розбір.\n\n"
            "/start – почати заново\n/profile – профіль, ліміти та реферали\n/compare – порівняти 2 продукти\n/history – історія\n/buy – купити бонусні скани\n/settings – мова, алергії та режими"
        ),
        "too_long": "⚠️ Занадто довго. Максимум {n} символів.",
        "send_text": "✍️ Напишіть алергії текстом або напишіть <b>Ні</b>.",
        "cmd_start": "Почати / Скидання",
        "cmd_settings": "Мова, алергії та режими безпеки",
        "cmd_help": "Як користуватися",
        "cmd_profile": "Профіль, ліміти та реферали",
        "cmd_history": "Історія сканувань",
        "cmd_compare": "Порівняти 2 відскановані продукти",
        "cmd_buy": "Купити незгораємі бонусні скани",
        "processing": "⏳ Обробляю зображення та витягую склад...",
        "processing_text": "⏳ Аналізую вставлений список інгредієнтів (INCI)...",
        "error": "❌ Під час аналізу сталася помилка. Будь ласка, спробуйте ще раз.",
        "limit_reached": (
            "⏳ Ви використали всі безкоштовні сканування на сьогодні ({n}/{n}), а бонусних сканів — 0.\n"
            "Повертайтеся завтра за {n} новими безкоштовними сканами, запросіть друга за +5 бонусних сканів або оберіть пакет нижче! 💙"
        ),
        "not_a_list": "⚠️ <b>Не вдалося прочитати список інгредієнтів.</b>\n{reason}\n\nБудь ласка, надішліть чіткіше, добре освітлене фото.",
        "lbl_traffic": "Оцінка світлофора",
        "light_green": "Зелений (Безпечно)",
        "light_yellow": "Жовтий (Обережно)",
        "light_red": "Червоний (Високий ризик)",
        "lbl_score": "Оцінка безпеки",
        "lbl_verdict": "Висновок",
        "lbl_breakdown": "Детальний розбір",
        "no_details": "Деталі про інгредієнти недоступні.",
        "disclaimer": "Лише для інформації - не є медичною порадою.",
        "btn_scan": "📸 Сканувати продукт",
        "btn_compare": "⚖️ Порівняти",
        "btn_profile": "👤 Профіль і ліміти",
        "btn_history": "🕘 Моя історія",
        "btn_buy": "⭐ Купити скани",
        "btn_menu_settings": "⚙️ Налаштування",
        "scan_intro": (
            "📸 <b>Сканування продукту (Фото або Текст)</b>\n\n"
            "• <b>Фото:</b> Надішліть чітке фото розділу <b>Ingredients / INCI</b> на етикетці.\n"
            "• <b>Онлайн-покупки:</b> Скопіюйте та вставте список інгредієнтів (INCI) текстом із <i>Farmacia Tei, Dr. Max, Notino, eMAG</i> тощо.\n\n"
            "💡 Порада: уникайте відблисків на фото або вставте щонайменше 2–3 інгредієнти через кому."
        ),
        "profile": (
            "👤 <b>Профіль і ліміти</b>\n\n"
            "🌐 Мова: {language}\n"
            "🤧 Алергії: {allergies}\n"
            "🛡️ Режими безпеки: {modes}\n\n"
            "📸 Безкоштовних сканів сьогодні: <b>{scans}</b>\n"
            "⭐ Бонусних сканів (не згорають): <b>{bonus}</b>\n"
            "🗂 Усього сканувань: <b>{total}</b>\n\n"
            "🤝 <b>Реферальна програма</b>\n"
            "👥 Запрошено друзів: <b>{referrals}</b>\n"
            "🔗 Ваше посилання: <code>{ref_link}</code>\n"
            "<i>Запросіть друга → ви обоє отримаєте <b>+5 бонусних сканів</b> після його першого сканування!</i>"
        ),
        "history_title": "🕘 <b>Моя історія</b>\nОстанні сканування — натисніть, щоб відкрити звіт:",
        "history_empty": "🕘 <b>Сканувань ще немає.</b>\nНадішліть фото складу або вставте список INCI, щоб почати!",
        "history_missing": "⚠️ Це сканування більше недоступне.",
        "scan_untitled": "Скан",
        "unknown_product": "Невідомий продукт",
        "lbl_alerts": "Особисті та профільні попередження",
        "lbl_irritants": "Позначені інгредієнти",
        "lbl_red": "Інгредієнти високого ризику",
        "lbl_yellow": "Інгредієнти з обережністю",
        "lbl_safe": "Безпечні інгредієнти",
        "lbl_alternatives": "Аптечні альтернативи",
        "no_ingredients_found": (
            "⚠️ <b>На цьому фото не знайдено список інгредієнтів.</b>\n\n"
            "Я ніколи не вгадую склад за брендом чи лицьовою стороною упаковки.\n"
            "📸 Будь ласка, чітко сфотографуйте розділ <b>«Ingredients» / INCI</b> на звороті етикетки та надішліть знову."
        ),
        "no_ingredients_text": (
            "⚠️ <b>У вашому повідомленні не виявлено списку косметичних інгредієнтів (INCI).</b>\n\n"
            "Скан не було списано. Будь ласка, вставте реальний склад INCI (наприклад, <i>Aqua, Glycerin, Niacinamide, Parfum...</i>) або надішліть чітке фото етикетки."
        ),
        "rule_formaldehyde": "Донор формальдегіду (сильний алерген / сенсибілізатор).",
        "rule_banned": "Обмежена або високоризикована речовина за нормами ЄС.",
        "rule_uv_filter": "Спірний хімічний УФ-фільтр (потенційний ендокринний / подразливий ризик).",
        "rule_fragrance": "Ароматизатор / декларований алерген (можлива сенсибілізація шкіри).",
        "rule_sulfate": "Агресивний сульфат (може пересушувати та подразнювати шкіру).",
        "rule_alcohol": "Підсушувальний спирт (може викликати подразнення і сухість).",
        "rule_peg_paraben": "ПЕГ / парабен (помірний ризик подразнення або регуляторні обмеження).",
        "rule_peg": "Емульгатор ПЕГ (може підвищувати проникність шкіри / ризик домішок).",
        "rule_paraben": "Консервант парабен (помірний ризик подразнення або регуляторні обмеження).",
        "rule_bht_bha": "Синтетичний антиоксидант (BHT/BHA — потенційний ендокринний дизраптор).",
        "rule_aluminum": "Сіль алюмінію в антиперспірантах (обережно для чутливої шкіри).",
        "rule_microplastic": "Синтетичний мікропластик.",
        "rule_petrochemical": "Оклюзивний нафтохімічний компонент.",
        "rule_allergy": "Збігається з вашою особистою алергією.",
        "rule_pregnancy": "Не рекомендується під час вагітності та грудного вигодовування.",
        "rule_comedogenic": "Комедогенний компонент (може забивати пори при схильності до акне).",
        "rule_sulfate_silicone": "Сульфат / нерозчинний силікон (позначений вашим режимом для волосся).",
        "report_title": "Аналіз складу",
        "btn_ask": "💬 Запитати про продукт",
        "btn_alternatives": "💊 Підібрати альтернативи",
        "btn_cancel": "❌ Скасувати",
        "qa_prompt": (
            "💬 <b>Запитайте про цей продукт</b>\n\n"
            "Напишіть будь-яке запитання щодо цього складу (наприклад, чи підходить для чутливої шкіри, під час вагітності, при акне або навіщо потрібен певний інгредієнт).\n"
            "Натисніть <b>Скасувати</b>, коли закінчите."
        ),
        "qa_cancelled": "✅ Режим запитань закрито.",
        "qa_send_text": "✍️ Будь ласка, напишіть запитання текстом або натисніть <b>Скасувати</b>.",
        "qa_error": "❌ Не вдалося відповісти на запитання. Будь ласка, спробуйте ще раз.",
        "alt_loading": "💊 Підбираю альтернативи з аптек Румунії...",
        "alt_empty": "ℹ️ Не вдалося підібрати конкретні аптечні альтернативи для цієї формули.",
        "alt_error": "❌ Не вдалося підібрати альтернативи зараз. Будь ласка, спробуйте ще раз.",
        "cmp_need_two": "⚖️ <b>Недостатньо сканувань для порівняння.</b>\nВ історії має бути щонайменше <b>2 завершені скани</b>. Спочатку відскануйте два продукти!",
        "cmp_pick1": "⚖️ <b>Порівняння 2 продуктів — Крок 1/2</b>\nОберіть <b>Продукт №1</b> із нещодавніх сканувань:",
        "cmp_pick2": "⚖️ <b>Порівняння 2 продуктів — Крок 2/2</b>\nПродукт №1: <b>{p1}</b>\nТепер оберіть <b>Продукт №2</b>:",
        "cmp_loading": "⚖️ Порівнюю продукти...",
        "cmp_cancelled": "✅ Порівняння скасовано.",
        "cmp_title": "⚖️ <b>Порівняння продуктів</b>",
        "cmp_p1": "Продукт №1",
        "cmp_p2": "Продукт №2",
        "cmp_winner": "🏆 <b>Переможець:</b>",
        "cmp_tie": "🤝 <b>Нічия</b>",
        "cmp_diffs": "🔍 <b>Ключові відмінності:</b>",
        "cmp_verdict": "📝 <b>Підсумковий висновок:</b>",
        "cmp_error": "❌ Не вдалося порівняти продукти зараз. Будь ласка, спробуйте ще раз.",
        "buy_menu": (
            "⭐ <b>Купити бонусні скани</b>\n\n"
            "Бонусні скани <b>ніколи не згорають</b> опівночі та використовуються автоматично після 3 щоденних безкоштовних сканів.\n\n"
            "Оберіть пакет нижче (оплата через Telegram Stars):"
        ),
        "btn_pack_10": "⭐ 10 бонусних сканів — 25 Stars",
        "btn_pack_30": "🌟 30 бонусних сканів — 60 Stars",
        "inv_title_10": "10 бонусних сканів",
        "inv_desc_10": "10 незгораємих бонусних сканувань складу (за фото або текстом INCI).",
        "inv_title_30": "30 бонусних сканів",
        "inv_desc_30": "30 незгораємих бонусних сканувань складу (за фото або текстом INCI).",
        "pay_success": "🎉 <b>Оплата успішна!</b>\nНараховано <b>+{added} бонусних сканів</b>.\n⭐ Новий бонусний баланс: <b>{balance}</b>",
        "pay_duplicate": "ℹ️ Цей платіж уже було зараховано на ваш баланс.",
        "ref_reward_referee": "🎁 <b>Реферальний бонус!</b> Ви виконали перше сканування та отримали <b>+{n} бонусних сканів</b>!",
        "ref_reward_referrer": "🎉 <b>Реферальна нагорода!</b> Запрошений друг виконав перше сканування — вам нараховано <b>+{n} бонусних сканів</b>!",
        "bonus_gift_notify": "🎁 <b>Вам нараховано +{amount} бонусних сканів!</b>\n⭐ Новий бонусний баланс: <b>{balance}</b>",
    },
}
