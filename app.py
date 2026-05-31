import streamlit as st
import requests
import re

st.set_page_config(page_title="مساعدك الطبي", page_icon="⚕️", layout="centered")

SYSTEM_PROMPT = """أنت مساعد طبي ذكي. مهمتك الوحيدة هي تحديد التخصص الطبي المناسب للمريض.

خطوات العمل:
1. اقرأ أعراض المريض
2. اسأل سؤالاً واحداً فقط لجمع معلومات إضافية
3. بعد سؤالين أو ثلاثة، قدّم توصيتك النهائية بهذا الشكل الحرفي فقط:

✅ التخصص المناسب: [اسم التخصص]
👨‍⚕️ نوع الطبيب: [مثال: طبيب عظام]
📋 السبب: [جملة واحدة مختصرة]

قائمة التخصصات الطبية — يجب الاختيار منها فقط:
- أعراض القلب (خفقان، ألم صدر، ضيق تنفس، دوخة) → طب القلب والأوعية الدموية
- أعراض العظام والمفاصل (ألم ركبة، كسر، خشونة، ظهر) → طب العظام والمفاصل
- أعراض الجهاز الهضمي (ألم بطن، إسهال، إمساك، حرقة) → طب الجهاز الهضمي
- أعراض الجلد (طفح، حكة، حبوب، تساقط شعر) → طب الجلدية
- أعراض العيون (ضعف بصر، احمرار، ألم عين) → طب العيون
- أعراض الأذن والأنف والحنجرة (صعوبة بلع، طنين، التهاب حلق) → طب الأذن والأنف والحنجرة
- أعراض المسالك البولية (ألم تبول، دم في البول) → طب المسالك البولية
- أعراض الأعصاب (صداع مزمن، تنميل، رعشة، دوار) → طب الأعصاب
- أعراض الغدد والسكري (تعب، عطش، زيادة وزن) → طب الغدد الصماء والسكري
- أعراض نفسية (قلق، اكتئاب، أرق، توتر) → الطب النفسي
- أعراض الأطفال (أقل من 14 سنة) → طب الأطفال
- أعراض النساء (دورة، حمل، مبايض) → طب النساء والتوليد
- أعراض الرئة (سعال مزمن، ربو، بلغم) → طب الأمراض الصدرية
- أعراض عامة غير محددة → الطب العام

قواعد صارمة جداً:
- اكتب بالعربية فقط — ممنوع أي كلمة صينية أو روسية أو إنجليزية أو لاتينية
- ردودك قصيرة ومركزة — لا شرح زائد
- إذا طلب المريض نصيحة، أجبه بجملتين فقط ثم اسأله عن أعراضه
- لا تشخيص طبي إطلاقاً، فقط توجيه للتخصص
- إذا طلب المريض تشخيصاً محدداً، اعتذر بلطف وقل: "لا أستطيع تشخيص حالتك، لكن يمكنني إرشادك للتخصص المناسب" ثم اسأله عن أعراضه
- سؤال واحد فقط في كل رسالة
- 🚨 اذهب للطوارئ فوراً: فقط عند ألم صدر شديد مفاجئ، صعوبة تنفس حادة، إغماء، نزيف شديد، أو شلل مفاجئ
"""

# الـ Key يُقرأ من Streamlit Secrets (آمن) أو من الكود مباشرة
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = ""  # API key is loaded from Streamlit Secrets when deployed

def ask_gemini(messages):
    try:
        system_text = ""
        groq_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                groq_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_text}] + groq_messages,
            "temperature": 0.3,
            "max_tokens": 500
        }
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ حدث خطأ: {str(e)}"

# ── Session ───────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');
* { font-family: 'Tajawal', sans-serif !important; box-sizing: border-box; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #f4f7f9 !important; direction: rtl; }
.block-container { padding: 0 !important; max-width: 780px !important; margin: 0 auto !important; }
section.main > div { padding: 0 !important; }

.app-header {
    background: linear-gradient(135deg, #0d2137, #0a7c6e);
    padding: 20px 24px 16px; text-align: center;
    position: sticky; top: 0; z-index: 100;
}
.app-header h1 { color: white !important; font-size: 1.6rem !important; font-weight: 800 !important; margin: 4px 0 !important; }
.app-header p { color: rgba(255,255,255,.75); font-size: .83rem; margin: 0; }
.gold { width: 36px; height: 3px; background: #c9a84c; margin: 8px auto 0; border-radius: 2px; }

.chat-wrap { padding: 14px 16px 160px; display: flex; flex-direction: column; gap: 10px; }

.brow { display: flex; flex-direction: column; }
.urow { align-items: flex-start; }
.botrow { align-items: flex-end; }
.lbl { font-size: .68rem; color: #8a99a8; margin-bottom: 2px; }
.bbl { max-width: 80%; padding: 11px 15px; font-size: .93rem; line-height: 1.75; text-align: right; word-break: break-word; border-radius: 16px; }
.ub { background: linear-gradient(135deg,#0a7c6e,#0d9e8c); color: white; border-radius: 16px 16px 16px 3px; box-shadow: 0 3px 12px rgba(10,124,110,.25); }
.bb { background: white; color: #0d2137; border-radius: 16px 16px 3px 16px; border: 1px solid #dce5ec; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.eb { background: linear-gradient(135deg,#c0392b,#e74c3c); color: white; border-radius: 16px 16px 3px 16px; }

.welcome-card { background: #e6f5f3; border: 1px solid rgba(10,124,110,.2); border-radius: 12px; padding: 14px 18px; text-align: center; color: #0a7c6e; font-size: .88rem; line-height: 1.7; }
.welcome-card strong { font-weight: 700; display: block; margin-bottom: 3px; }

/* typing dots */
.typing-wrap { display: flex; flex-direction: column; align-items: flex-end; }
.typing { display: flex; align-items: center; gap: 5px; padding: 12px 16px; background: white; border-radius: 16px 16px 3px 16px; border: 1px solid #dce5ec; }
.typing span { width: 8px; height: 8px; background: #0a7c6e; border-radius: 50%; display: inline-block; animation: bounce .9s infinite; }
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }

/* Fixed input */
.fixed-bar {
    position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
    width: 100%; max-width: 780px;
    background: #f4f7f9; border-top: 1.5px solid #dce5ec;
    padding: 10px 16px 14px; box-shadow: 0 -3px 16px rgba(0,0,0,.07); z-index: 9999;
}
.hint { font-size: .72rem; color: #8a99a8; text-align: right; margin-bottom: 6px; }
div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
.stTextInput > div > div > input {
    direction: rtl !important; text-align: right !important;
    border: 2px solid #dce5ec !important; border-radius: 12px !important;
    padding: 10px 14px !important; font-size: .93rem !important;
    background: white !important; color: #0d2137 !important;
}
.stTextInput > div > div > input:focus { border-color: #0a7c6e !important; box-shadow: 0 0 0 3px rgba(10,124,110,.1) !important; }
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg,#0a7c6e,#0d9e8c) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    padding: 10px 24px !important; font-size: .95rem !important; font-weight: 700 !important;
    width: 100% !important; margin-top: 8px !important;
    box-shadow: 0 3px 10px rgba(10,124,110,.3) !important;
}
.stButton > button {
    background: transparent !important; color: #8a99a8 !important;
    border: 1.5px solid #dce5ec !important; border-radius: 9px !important;
    padding: 6px !important; font-size: .8rem !important; width: 100% !important;
    margin-top: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <span style="font-size:1.8rem">⚕️</span>
    <h1>مساعدك الطبي الذكي</h1>
    <p>أخبرني بأعراضك وسأرشدك إلى التخصص الطبي المناسب</p>
    <div class="gold"></div>
</div>
""", unsafe_allow_html=True)

# ── Chat ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

if not st.session_state.chat_history:
    st.markdown('<div class="welcome-card"><strong>👋 أهلاً وسهلاً!</strong>صف لي أعراضك بكل حرية، وسأسألك بعض الأسئلة ثم أرشدك إلى الطبيب المناسب.</div>', unsafe_allow_html=True)

for role, text in st.session_state.chat_history:
    fmt = text.replace('\n','<br>').replace('👨\u200d⚕️','<br>👨\u200d⚕️').replace('📋','<br>📋')
    is_em = "طوارئ" in text or "🚨" in text
    if role == "user":
        st.markdown(f'<div class="brow urow"><div class="lbl">أنت</div><div class="bbl ub">{fmt}</div></div>', unsafe_allow_html=True)
    else:
        cls = "eb" if is_em else "bb"
        st.markdown(f'<div class="brow botrow"><div class="lbl">⚕️ المساعد الطبي</div><div class="bbl {cls}">{fmt}</div></div>', unsafe_allow_html=True)

# typing dots placeholder
typing_slot = st.empty()

st.markdown('</div>', unsafe_allow_html=True)

# ── Fixed input ───────────────────────────────────────────────────────────────
st.markdown('<div class="fixed-bar"><div class="hint">اكتب أعراضك باللغة العربية...</div>', unsafe_allow_html=True)

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("msg", placeholder="مثال: عندي ألم في صدري...", label_visibility="collapsed")
    submitted = st.form_submit_button("إرسال ➤")

if submitted and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append(("user", user_input))
    with typing_slot:
        st.markdown('<div class="typing-wrap"><div class="lbl">⚕️ المساعد الطبي</div><div class="typing"><span></span><span></span><span></span></div></div>', unsafe_allow_html=True)
    reply = ask_gemini(st.session_state.messages)
    typing_slot.empty()
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.chat_history.append(("bot", reply))
    st.rerun()

if st.session_state.chat_history:
    if st.button("🔄 محادثة جديدة"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.chat_history = []
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)