import json
import re
import ast
import operator
import datetime
from http.server import BaseHTTPRequestHandler

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
       ast.USub: operator.neg, ast.UAdd: operator.pos}

def safe_math(text):
    text = text.lower().replace(",", "").replace("×", "*").replace("÷", "/")
    pct = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)\s*", text)
    if pct:
        return float(pct.group(1)) / 100 * float(pct.group(2))
    candidate = re.sub(r"[^0-9.+*/()%\-\s]", "", text)
    if not candidate.strip() or not re.search(r"[+*/%]", candidate):
        return None
    try:
        tree = ast.parse(candidate, mode="eval")
        def calc(n):
            if isinstance(n, ast.Expression): return calc(n.body)
            if isinstance(n, ast.Constant) and type(n.value) in (int, float): return n.value
            if isinstance(n, ast.BinOp) and type(n.op) in OPS:
                a, b = calc(n.left), calc(n.right)
                if abs(a) > 1e12 or abs(b) > 1e12: raise ValueError()
                return OPS[type(n.op)](a, b)
            if isinstance(n, ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](calc(n.operand))
            raise ValueError()
        result = calc(tree)
        if abs(result) > 1e15: return None
        return result
    except Exception:
        return None

FACTS = [
    (("capital of nigeria", "nigeria capital", "capital naija", "capital for nigeria"), "The capital of Nigeria is Abuja.", "Capital of Nigeria na Abuja."),
    (("wetin be jamb", "what is jamb", "jamb stand for", "what does jamb stand"), "JAMB means Joint Admissions and Matriculation Board. It conducts the UTME entrance examination for tertiary institutions in Nigeria, scored out of 400.", "JAMB na Joint Admissions and Matriculation Board. Dem dey run UTME entrance exam for higher institutions for Nigeria, and the score dey out of 400."),
    (("currency of nigeria", "nigeria currency", "money in nigeria", "naira"), "Nigeria's currency is the naira (₦). One naira is 100 kobo.", "Nigeria money na naira (₦). One naira na 100 kobo."),
    (("how many states", "number of states", "states in nigeria"), "Nigeria has 36 states and the Federal Capital Territory, Abuja.", "Nigeria get 36 states plus Federal Capital Territory, Abuja."),
    (("languages in nigeria", "language nigeria", "official language"), "English is Nigeria's official language. Hausa, Yoruba and Igbo are major indigenous languages, and Nigeria has hundreds of languages.", "English na Nigeria official language. Hausa, Yoruba and Igbo na major local languages, and Nigeria get hundreds of languages."),
    (("nigerian pidgin", "what is pidgin", "pidgin english"), "Nigerian Pidgin is an English-based creole used widely across Nigeria to communicate across language groups.", "Nigerian Pidgin na English-based language wey people for Nigeria dey use communicate across different language groups."),
    (("largest city", "biggest city", "tell me about lagos", "lagos capital"), "Lagos is Nigeria's largest city and commercial centre. Abuja has been the national capital since 1991.", "Lagos na Nigeria biggest city and business centre. Abuja don be national capital since 1991."),
    (("waec", "neco", "wassce"), "WAEC runs the WASSCE and NECO runs the SSCE; both are secondary-school leaving examinations.", "WAEC dey run WASSCE and NECO dey run SSCE; both na secondary-school final exams."),
    (("time zone", "nigeria time zone", "utc plus one"), "Nigeria uses West Africa Time (WAT), UTC+1, throughout the year.", "Nigeria dey use West Africa Time (WAT), UTC+1, throughout the year."),
    (("emergency number", "call police", "number in emergency"), "Nigeria's national emergency number is 112.", "Nigeria national emergency number na 112."),
    (("jollof", "jollof rice"), "Jollof rice is a popular West African dish. Nigerian party jollof is especially known for its smoky flavour.", "Jollof rice na popular West African food. Nigerian party jollof dey famous for im smoky taste."),
    (("nigerian flag", "flag of nigeria"), "The Nigerian flag has three vertical bands: green, white and green. Green represents agriculture and natural wealth; white represents peace.", "Nigerian flag get three vertical bands: green, white and green. Green represent farming and natural wealth; white represent peace."),
    (("national motto", "nigeria motto"), 'Nigeria\'s national motto is "Unity and Faith, Peace and Progress".', 'Nigeria national motto na "Unity and Faith, Peace and Progress".'),
]
JOKES = ["Why did the generator go to school? To get more power.", "I told my phone I'd charge it later. It asked, 'Is NEPA aware of this plan?'", "Why was the calculator calm in Lagos traffic? It took things one step at a time."]

def answer(message):
    raw = message.strip()
    q = raw.lower()
    pidgin = any(w in q for w in ("wetin", "dey", "abeg", "na ", "fit ", "how far", "wahala", "sabi", "jollof"))
    if not raw: return "Abeg type a question first." if pidgin else "Please type a question first."
    if re.search(r"\b(hi|hello|hey|how far|wassup|how you dey)\b", q):
        return "How far! I be Naija Brain. Wetin you wan know?" if pidgin else "Hello! I'm Naija Brain, built in Nigeria. What would you like to know?"
    if any(x in q for x in ("who are you", "your name", "wetin be your name", "who made you", "who built you")):
        return "I be Naija Brain, a Nigerian response engine. I use my own rules and knowledge base, no outside AI service." if pidgin else "I'm Naija Brain, a Nigerian response engine using my own rules and knowledge base, not an outside AI service."
    if any(x in q for x in ("thank", "no wahala", "oshe", "dalu")):
        return "No wahala!" if pidgin else "You're welcome!"
    if any(x in q for x in ("bye", "goodbye", "see you")):
        return "We go see later!" if pidgin else "Goodbye! Come back anytime."
    if "joke" in q or "make me laugh" in q:
        return JOKES[sum(map(ord, q)) % len(JOKES)]
    if any(x in q for x in ("what time", "time now", "what date", "today's date", "todays date", "what day is")):
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))
        return "Nigeria time na " + now.strftime("%I:%M %p, %A %d %B %Y") + " (WAT)." if pidgin else "In Nigeria (WAT), it is " + now.strftime("%I:%M %p on %A, %d %B %Y") + "."
    result = safe_math(q)
    if result is not None:
        return str(int(result) if float(result).is_integer() else round(result, 6))
    for keys, en, pcm in FACTS:
        if any(k in q for k in keys):
            return pcm if pidgin else en
    if q in ("help", "what can you do", "wetin you fit do"):
        return "I fit answer some Nigeria questions, do maths, tell joke, give Nigeria time, and understand Pidgin." if pidgin else "I can answer selected questions about Nigeria, do calculations, tell jokes, and give the current time in Nigeria. I also understand some Pidgin."
    return "I never get that one yet, and I no wan guess. Try ask about Nigeria, JAMB, WAEC, naira, Pidgin, or do calculation." if pidgin else "I don't have that answer yet, and I'd rather say so than guess. Try asking about Nigeria, JAMB, WAEC, the naira, Pidgin, or a calculation."

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path not in ("/api/chat", "/"):
            return self._send(404, {"error": "Not found"})
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 4000)
            payload = json.loads(self.rfile.read(length) or b"{}")
            message = str(payload.get("message", ""))[:500]
            result = {"reply": answer(message)}
            self._send(200, result)
        except (ValueError, TypeError):
            self._send(400, {"error": "Bad request"})
    def do_GET(self):
        self._send(200, {"status": "ok", "service": "Naija Brain API"})
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args): pass
