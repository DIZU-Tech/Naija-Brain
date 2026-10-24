"""Self-contained Jarvis Brain (JB) v0.9 + Jarvis Response Engine (JRE) research core.

No external LLM, search, or database service is called by this module.
"""
from __future__ import annotations
import ast, datetime as dt, json, operator, os, re, sqlite3, threading, time, unicodedata
from contextlib import contextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

LOCK = threading.RLock()
FACTS = [
 {"id":"nigeria","topic":"Nigeria","aliases":["Nigeria","Naija","country in West Africa"],"en":"Nigeria is a federal republic in West Africa. Its capital is Abuja, its largest city is Lagos, and English is its official language.","pcm":"Nigeria na federal republic for West Africa. Abuja na im capital, Lagos na im biggest city, and English na im official language."},
 {"id":"capital","topic":"Capital of Nigeria","aliases":["capital of Nigeria","Abuja","FCT"],"en":"The capital of Nigeria is Abuja. The seat of government moved there from Lagos in 1991.","pcm":"Capital of Nigeria na Abuja. Government move from Lagos go Abuja for 1991."},
 {"id":"independence","topic":"Nigerian independence","aliases":["independence","1960","October 1"],"en":"Nigeria became independent from Britain on 1 October 1960 and became a republic in 1963.","pcm":"Nigeria get independence from Britain on 1 October 1960, and e become republic for 1963."},
 {"id":"states","topic":"States of Nigeria","aliases":["states in Nigeria","36 states","geopolitical zones"],"en":"Nigeria has 36 states and the Federal Capital Territory (FCT), Abuja. The states are grouped into six geopolitical zones.","pcm":"Nigeria get 36 states plus Federal Capital Territory (FCT), Abuja. Dem group the states into six geopolitical zones."},
 {"id":"naira","topic":"Nigerian currency","aliases":["naira","currency of Nigeria","kobo"],"en":"Nigeria's currency is the naira (₦). One naira is 100 kobo.","pcm":"Nigeria money na naira (₦). One naira na 100 kobo."},
 {"id":"jamb","topic":"JAMB and UTME","aliases":["JAMB","UTME","Joint Admissions and Matriculation Board"],"en":"JAMB means Joint Admissions and Matriculation Board. It administers the UTME used for admission into many Nigerian tertiary institutions.","pcm":"JAMB na Joint Admissions and Matriculation Board. Dem dey run UTME wey many higher institutions for Nigeria dey use for admission."},
 {"id":"waec","topic":"WAEC and WASSCE","aliases":["WAEC","WASSCE","West African Examinations Council"],"en":"WAEC stands for West African Examinations Council and administers WASSCE. NECO runs the Senior School Certificate Examination as well.","pcm":"WAEC na West African Examinations Council and dem dey run WASSCE. NECO dey run Senior School Certificate Examination too."},
 {"id":"pidgin","topic":"Nigerian Pidgin","aliases":["Pidgin","Nigerian Pidgin","Pidgin English"],"en":"Nigerian Pidgin is an English-based creole used widely across Nigeria to communicate across language groups.","pcm":"Nigerian Pidgin na English-based language wey people for Nigeria dey use communicate across different language groups."},
 {"id":"lagos","topic":"Lagos","aliases":["Lagos","largest city in Nigeria","commercial centre"],"en":"Lagos is Nigeria's largest city and a major commercial centre. Abuja has been the national capital since 1991.","pcm":"Lagos na Nigeria biggest city and major business centre. Abuja don be national capital since 1991."},
 {"id":"bola_tinubu","topic":"Bola Ahmed Tinubu","aliases":["Bola Tinubu","Bola Ahmed Tinubu","Tinubu","President Tinubu","Asiwaju"],"entity":"Bola Ahmed Tinubu","birth_date":"1952-03-29","en":"Bola Ahmed Tinubu was born on 29 March 1952.","pcm":"Bola Ahmed Tinubu born on 29 March 1952."},
 {"id":"remi_tinubu","topic":"Oluremi (Remi) Tinubu","aliases":["Remi Tinubu","Oluremi Tinubu","Oluremi Naomi Tinubu","First Lady","Tinubu wife"],"entity":"Oluremi Tinubu","birth_date":"1960-09-21","en":"Oluremi (Remi) Tinubu was born on 21 September 1960.","pcm":"Oluremi (Remi) Tinubu born on 21 September 1960."},
 {"id":"ai","topic":"Artificial intelligence","aliases":["artificial intelligence","AI","machine intelligence"],"en":"Artificial intelligence (AI) is a field of computing that builds systems able to perform tasks such as recognising patterns, understanding language, making predictions, or planning. Not every AI system is a large language model.","pcm":"Artificial intelligence (AI) na computer technology wey dey do work like recognise patterns, understand language, make predictions, or plan. No be every AI be large language model."},
 {"id":"inflation","topic":"Inflation","aliases":["inflation","rising prices","cost of living"],"en":"Inflation is a sustained rise in the general price level of goods and services. When prices rise faster than income, money buys less than before. Current inflation figures require a dated source.","pcm":"Inflation na when price of goods and services dey rise generally. If price rise pass income, money no go buy as much as before. Current figures need dated source."},
 {"id":"photosynthesis","topic":"Photosynthesis","aliases":["photosynthesis","how plants make food"],"en":"Photosynthesis is the process by which plants, algae, and some bacteria use light energy to turn carbon dioxide and water into energy-rich sugars, releasing oxygen.","pcm":"Photosynthesis na process wey plants and some other organisms dey use light turn carbon dioxide and water into sugar, while oxygen dey come out."},
 {"id":"world_war_two","topic":"World War II","aliases":["World War II","WWII","Second World War"],"en":"World War II lasted from 1939 to 1945 and involved countries across multiple continents.","pcm":"World War II last from 1939 reach 1945, and countries for different continents join am."},
]
STOP={"what","is","are","was","were","the","a","an","of","to","for","in","on","at","and","or","how","who","when","where","why","can","you","me","tell","about","please","abeg","wetin","be","na","i","it","do","does","did","this","that","he","she","his","her","old","age"}
PIDGIN={"wetin","dey","abeg","wahala","naija","sabi","fit","una","dem","sef","sha","oya","abi","wey","wan","comot","gist","jare","howfar","howbody"}
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.Mod:operator.mod,ast.USub:operator.neg,ast.UAdd:operator.pos}

def norm(s):
 s=unicodedata.normalize("NFKC",str(s or "")).replace("’","'").replace("–","-").replace("—","-")
 return re.sub(r"\s+"," ",s).strip()
def words(s): return [x for x in re.findall(r"[a-z0-9]+",s.lower()) if x not in STOP and len(x)>1]
def language(s):
 t=norm(s).lower(); w=set(re.findall(r"[a-z]+",t))
 return "pcm" if w & PIDGIN or any(x in t for x in ("how far","how you dey","as how na","no wahala")) else "en"
def intent(s):
 t=norm(s).lower().strip(" .!?")
 if not t:return "empty"
 if t in {"hi","hello","hey","yo","sup","wassup","good morning","good afternoon","good evening","how far","how you dey","how body"} or re.match(r"^(hi+|hello+|hey+|yo|sup|wassup)\b",t):return "greeting"
 if t in {"as how na","as how","what do you mean","what you mean","how so"}:return "clarification"
 if re.search(r"\b(thanks|thank you|thank u|appreciate|oshe|dalu|no wahala)\b",t):return "thanks"
 if re.match(r"^(bye|goodbye|see you|later|good night)\b",t):return "goodbye"
 if re.search(r"\b(who are you|what are you|what is your name|who made you|who built you|who created you)\b",t):return "identity"
 if re.search(r"\b(what can you do|how can you help|your capabilities|wetin you fit do)\b",t):return "capabilities"
 if re.search(r"\b(my name is|call me|my name na)\b",t):return "set_name"
 if re.search(r"\b(what is my name|who am i|do you know my name|wetin be my name)\b",t):return "ask_name"
 if re.search(r"\b(how bad are you|you are bad|you suck|useless|rubbish|stupid|terrible|wrong answer|that is wrong)\b",t):return "negative_feedback"
 if re.search(r"\b(joke|make me laugh|tell me something funny)\b",t):return "joke"
 if re.search(r"\b(what time|time now|what date|today's date|todays date|what day is it)\b",t):return "time"
 if re.search(r"\b(tell me more|more about that|go on|continue|expand on that|gist me more)\b",t):return "continue"
 if t in {"wow","jesus","ok","okay","alright","cool","i see","hmm","ah","oh","nice","fine","noted","sure","yes","yeah","yep","no","nope","oya","ehen","abi","lol","haha"}:return "acknowledgment"
 if re.search(r"\b(everything|all knowledge|know everything)\b",t):return "broad_request"
 return "question"
def qtype(s):
 t=s.lower()
 for name,pat in [("age",r"\bhow old\b|\bage of\b|\bdate of birth\b"),("who",r"\bwho\b"),("when",r"\bwhen\b|\bwhat year\b"),("where",r"\bwhere\b"),("why",r"\bwhy\b"),("howto",r"\bhow\b|\bsteps\b|\bguide\b"),("definition",r"\bwhat is\b|\bmeaning of\b|\bexplain\b|\bdefine\b"),("quantity",r"\bhow many\b|\bhow much\b")]:
  if re.search(pat,t):return name
 return "general"
def calc(s):
 t=s.lower().replace(",","").replace("×","*").replace("÷","/").replace("₦","").replace("naira","")
 m=re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s*of\s*(\d+(?:\.\d+)?)",t)
 if m:return fmt(float(m.group(1))*float(m.group(2))/100)
 for pat,rep in [(r"\bplus\b","+"),(r"\bminus\b","-"),(r"\b(?:times|multiplied by)\b","*"),(r"\bdivided by\b","/"),(r"\bto the power of\b","**"),(r"\^","**")]:t=re.sub(pat,rep,t)
 chunks=[c.strip() for c in re.findall(r"[\d.\s+\-*/()%]+",t) if re.search(r"\d",c) and re.search(r"[+*/%]|(?<=\d)-",c)]
 if not chunks:return None
 def ev(n):
  if isinstance(n,ast.Expression):return ev(n.body)
  if isinstance(n,ast.Constant) and type(n.value) in (int,float):return n.value
  if isinstance(n,ast.BinOp) and type(n.op) in OPS:
   a,b=ev(n.left),ev(n.right)
   if abs(a)>1e12 or abs(b)>1e12 or (isinstance(n.op,ast.Pow) and abs(b)>10):raise ValueError()
   return OPS[type(n.op)](a,b)
  if isinstance(n,ast.UnaryOp) and type(n.op) in OPS:return OPS[type(n.op)](ev(n.operand))
  raise ValueError()
 try:
  v=ev(ast.parse(max(chunks,key=len),mode="eval"))
  if not isinstance(v,(int,float)) or abs(v)>1e15:return None
  return fmt(v)
 except Exception:return None
def fmt(v):
 if isinstance(v,float) and v.is_integer():v=int(v)
 return f"{v:,}" if isinstance(v,int) else f"{round(v,6):,}"
def age(born,today=None):
 b=dt.date.fromisoformat(born); t=today or dt.date.today()
 return t.year-b.year-((t.month,t.day)<(b.month,b.day))

class ConversationStore:
 def __init__(self,path=None):
  self.path=path or os.getenv("NAIJA_BRAIN_DB_PATH") or ("/tmp/naija_brain.sqlite3" if os.getenv("VERCEL") else str(Path(__file__).resolve().parents[1]/"data"/"naija_brain.sqlite3"))
  if self.path!=":memory:":Path(self.path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:
   c.executescript("""
   CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,profile TEXT NOT NULL DEFAULT '{}',topic TEXT NOT NULL DEFAULT '',updated TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS turns(id INTEGER PRIMARY KEY AUTOINCREMENT,session TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,meta TEXT NOT NULL DEFAULT '{}',created TEXT NOT NULL);
   CREATE INDEX IF NOT EXISTS turns_session ON turns(session,id);
   CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,session TEXT,message TEXT,category TEXT,created TEXT);
   CREATE TABLE IF NOT EXISTS experiments(id INTEGER PRIMARY KEY AUTOINCREMENT,session TEXT,event TEXT,created TEXT);
   """)
 @contextmanager
 def db(self):
  c=sqlite3.connect(self.path,timeout=10);c.row_factory=sqlite3.Row
  try:yield c;c.commit()
  except Exception:c.rollback();raise
  finally:c.close()
 @staticmethod
 def now():return dt.datetime.now(dt.timezone.utc).isoformat()
 def ensure(self,s):
  with self.db() as c:c.execute("INSERT OR IGNORE INTO sessions(id,updated) VALUES(?,?)",(s,self.now()))
 def add(self,s,role,text,meta=None):
  now=self.now()
  with self.db() as c:
   c.execute("INSERT OR IGNORE INTO sessions(id,updated) VALUES(?,?)",(s,now))
   c.execute("INSERT INTO turns(session,role,content,meta,created) VALUES(?,?,?,?,?)",(s,role,text,json.dumps(meta or {},ensure_ascii=False),now))
   c.execute("UPDATE sessions SET updated=? WHERE id=?",(now,s))
 def context(self,s):
  with self.db() as c:
   row=c.execute("SELECT profile,topic FROM sessions WHERE id=?",(s,)).fetchone()
   turns=c.execute("SELECT role,content,meta FROM turns WHERE session=? ORDER BY id DESC LIMIT 12",(s,)).fetchall()
  turns=list(reversed(turns)); profile=json.loads(row["profile"] or "{}") if row else {}
  return {"profile":profile,"topic":row["topic"] if row else "", "turns":[dict(role=r["role"],content=r["content"],meta=json.loads(r["meta"] or "{}")) for r in turns]}
 def profile(self,s,p):
  with self.db() as c:c.execute("UPDATE sessions SET profile=?,updated=? WHERE id=?",(json.dumps(p,ensure_ascii=False),self.now(),s))
 def topic(self,s,t):
  if t:
   with self.db() as c:c.execute("UPDATE sessions SET topic=?,updated=? WHERE id=?",(t,self.now(),s))
 def log(self,table,s,payload):
  col="message,category" if table=="feedback" else "event"
  with self.db() as c:
   if table=="feedback":c.execute("INSERT INTO feedback(session,message,category,created) VALUES(?,?,?,?)",(s,payload,"negative",self.now()))
   else:c.execute("INSERT INTO experiments(session,event,created) VALUES(?,?,?)",(s,json.dumps(payload,ensure_ascii=False),self.now()))

class UnderstandingEngine:
 def analyze(self,text):
  raw=norm(text); it=intent(raw); topic=""
  if re.search(r"\b(tinubu|remi|president|first lady)\b",raw,re.I):topic="tinubu"
  elif re.search(r"\b(nigeria|naija|jamb|waec|neco|naira|pidgin)\b",raw,re.I):topic="nigeria"
  elif re.search(r"\b(inflation|prices|cost of living)\b",raw,re.I):topic="inflation"
  return {"raw":raw,"normalized":raw.lower(),"intent":it,"qtype":qtype(raw),"language":language(raw),"topic":topic}
class LocalKnowledgeBase:
 def __init__(self,facts=None):self.facts=facts or FACTS
 def retrieve(self,query,limit=4):
  low=query.lower(); q=set(words(query)); ranked=[]
  for f in self.facts:
   fields=[f["topic"]]+f.get("aliases",[])+[f.get("en","")]
   score=0.0
   for field in fields:
    fw=set(words(field)); overlap=len(q&fw)
    if overlap:score=max(score,overlap/(max(len(q),1)**0.65)+overlap/max(len(fw),1)*0.45)
   for a in f.get("aliases",[]):
    a=a.lower()
    if re.search(r"(?<!\w)"+re.escape(a)+r"(?!\w)",low):
     strong=len(a.split())>1 or a in {"tinubu","remi","jamb","waec","lagos","abuja","naira","pidgin","inflation","photosynthesis"}
     if strong or len(q)<=4:score=max(score,6.5+min(len(a),30)/100)
   if low.strip() in [x.lower() for x in f.get("aliases",[])]:score=max(score,8.0)
   if score:ranked.append((score,f))
  ranked.sort(key=lambda x:x[0],reverse=True)
  return [{"score":round(s,3),"fact":f} for s,f in ranked[:limit]]
class DecisionEngine:
 def plan(self,u,ctx):
  i=u["intent"]; direct={"empty":"dialogue","greeting":"dialogue","thanks":"dialogue","goodbye":"dialogue","identity":"dialogue","capabilities":"dialogue","set_name":"profile","ask_name":"profile","negative_feedback":"feedback","acknowledgment":"dialogue","broad_request":"clarify","joke":"dialogue","time":"time","continue":"knowledge","clarification":"clarification"}
  if i in direct:return {"action":direct[i],"purpose":i,"confidence":.95}
  if u["qtype"]=="age":return {"action":"age","purpose":"answer_fact","confidence":.88}
  if calc(u["raw"]) is not None:return {"action":"calculation","purpose":"calculate","confidence":.99}
  if re.search(r"\b(current|currently|live|latest|today|right now|news|stocks?|share price|market price|exchange rate|price of|weather|score today)\b",u["raw"].lower()):return {"action":"current_unavailable","purpose":"no_live_data","confidence":.98}
  follow=bool(re.match(r"^(and |what about |how about |why |how old is he|how old is she|what about him|what about her|explain that|what does that mean|and his|and her)\b",u["raw"].lower()))
  if follow and ctx["topic"]:return {"action":"followup","purpose":"resolve_context","confidence":.74}
  return {"action":"retrieve","purpose":"answer_question","confidence":.68}
class ResponseValidator:
 def validate(self,reply,action,evidence):
  issues=[]
  if not reply or not reply.strip():issues.append("empty_response")
  if len(reply)>5000:issues.append("response_too_long")
  if action in {"retrieve","age","followup"} and not evidence and not any(x in reply.lower() for x in ("don't have enough","never get enough","more about what","can't verify")):issues.append("unsupported_factual_answer")
  if re.search(r"\b(i searched the web|according to the internet)\b",reply,re.I):issues.append("unsupported_capability_claim")
  return {"ok":not issues,"issues":issues}
class JarvisResponseEngine:
 def __init__(self,kb,store):self.kb=kb;self.store=store;self.validator=ResponseValidator()
 def respond(self,u,plan,ctx,sid):
  started=time.perf_counter(); action=plan["action"]; ev=[]; tool=None; source="jre_dialogue"
  prev=next((x["content"] for x in reversed(ctx["turns"][:-1]) if x["role"]=="assistant"),"")
  if action in {"retrieve","age","followup","knowledge"}:
   query=u["raw"]
   if action=="age" and re.search(r"tinubu|remi|oluremi|first lady",query,re.I):query="Bola Tinubu Remi Tinubu birth date"
   if action=="followup" and re.search(r"his wife|and his wife|what about his wife|what about remi",query,re.I):
    ev=[x for x in self.kb.retrieve("Remi Tinubu",8) if x["fact"]["id"]=="remi_tinubu"]
   elif action=="followup" and re.search(r"\b(he|him|his)\b",query,re.I) and ctx["topic"]=="tinubu":ev=self.kb.retrieve("Bola Tinubu",3)
   elif action=="followup" and re.search(r"\b(she|her)\b",query,re.I) and ctx["topic"]=="tinubu":ev=self.kb.retrieve("Remi Tinubu",3)
   else:ev=self.kb.retrieve(query,5)
   source="local_knowledge_base"
  if action=="time":tool=dt.datetime.now(ZoneInfo("Africa/Lagos")).strftime("%I:%M %p on %A, %d %B %Y")+" (West Africa Time, WAT).";source="local_tool:time"
  if action=="calculation":tool=calc(u["raw"]);source="local_tool:calculator"
  pcm=u["language"]=="pcm"; reply=""
  if action=="dialogue":
   if u["intent"]=="empty":reply="Abeg type your question first." if pcm else "Please type a message first."
   elif u["intent"]=="greeting":reply="How far! I be Naija Brain. Wetin dey your mind?" if pcm else "Hello! I'm Naija Brain, built in Nigeria. What would you like to know?"
   elif u["intent"]=="thanks":reply="No wahala!" if pcm else "You're welcome!"
   elif u["intent"]=="goodbye":reply="We go see later!" if pcm else "Goodbye! Take care."
   elif u["intent"]=="identity":reply="I be Naija Brain. JB/JRE na local code and local knowledge; I no dey call outside LLM APIs." if pcm else "I'm Naija Brain. JB/JRE uses local code and local knowledge; it does not call external LLM APIs."
   elif u["intent"]=="capabilities":reply="I fit handle supported facts, Pidgin, local maths, dates, and follow-up context. I go tell you when I no get enough evidence." if pcm else "I can handle supported facts, Pidgin, local calculations, dates, and contextual follow-ups. I'll say when I lack evidence."
   elif u["intent"]=="joke":reply="Why did the generator go to school? To get more power."
   elif u["intent"]=="time":reply=("Nigeria time na " if pcm else "In Nigeria, it is ")+str(tool)
   elif u["intent"]=="acknowledgment" and u["raw"].lower().startswith("wow"):reply="Yeah, that can be a lot 😄 Let's take it one step at a time." if not pcm else "E plenty sha 😄 Make we take am one step at a time."
   elif u["intent"]=="acknowledgment" and ("don't have" in prev.lower() or "never get" in prev.lower()):reply="I hear you. My last answer was too generic. Tell me the exact part you want to explore, and I'll try from what I actually know." if not pcm else "I hear you. My last answer too general. Tell me the exact part wey you wan know."
   else:reply="Okay. What would you like to explore next?" if not pcm else "Okay. Wetin you wan explore next?"
  elif action=="clarify":reply="Everything is a lot 😄 Pick a starting point—science, history, Nigeria, technology, school, or how the world works—and we'll explore it step by step." if not pcm else "Everything na plenty o 😄 Pick a starting point—science, history, Nigeria, technology, school, or how the world works—and we go explore am small small."
  elif action=="clarification":reply="I mean the system has limits: it can answer supported questions, but it cannot honestly claim to know every fact. Which part should I explain?" if not pcm else "I mean say the system get limit: e fit answer wetin e support, but e no fit claim say e know everything. Which part make I explain?"
  elif action=="feedback":
   reply="Fair question. I'm a limited, rule-based system—not a general-purpose trained language model. I should follow context, answer supported questions, and admit gaps. If I miss something, that's a bug to measure and fix." if not pcm else "Fair question o. I still be limited rule-based system, no be general trained language model. I suppose follow context and admit when I no know."
   self.store.log("feedback",sid,u["raw"])
  elif action=="profile":
   p=ctx["profile"]
   m=re.search(r"(?:my name is|call me|my name na)\s+([A-Za-z][A-Za-z'-]{0,39})",u["raw"],re.I)
   if u["intent"]=="set_name" and m:
    p["name"]=m.group(1)
    with self.store.db() as c:c.execute("UPDATE sessions SET profile=? WHERE id=?",(json.dumps(p),sid))
    reply=f"Nice to meet you, {p['name']}!"
   else:reply=(f"Your name is {p['name']}." if not pcm else f"Your name na {p['name']}.") if p.get("name") else ("I never know your name yet. Wetin I go call you?" if pcm else "I don't know your name yet. What should I call you?")
  elif action=="current_unavailable":reply="I can't verify live or current information because network retrieval is disabled by design. I won't invent a current figure; it needs a dated local data import." if not pcm else "I no fit verify live/current information because network retrieval no dey enabled. I no go invent figure; we need dated local data."
  elif action=="time":reply=("Nigeria time na " if pcm else "In Nigeria, it is ")+str(tool)
  elif action=="calculation":reply=str(tool) if tool is not None else ("I couldn't safely parse that calculation. Try writing the numbers and operation clearly." if not pcm else "I no fit parse that calculation safely. Abeg write the numbers and operation clearly.")
  elif action=="age":
   fact=next((x["fact"] for x in ev if x["fact"].get("birth_date") and x["fact"]["id"]==("remi_tinubu" if re.search(r"remi|oluremi|first lady|his wife",u["raw"],re.I) else "bola_tinubu")),None)
   if fact:
    a=age(fact["birth_date"]); today=dt.date.today().strftime("%d %B %Y")
    if fact["id"]=="bola_tinubu" and re.search(r"\btinubu\b",u["raw"],re.I) and not re.search(r"bola|remi|oluremi",u["raw"],re.I):
     remi=next(x["fact"] for x in ev if x["fact"]["id"]=="remi_tinubu")
     reply=f"If you mean Bola Ahmed Tinubu, he is {a} years old (born 29 March 1952). Remi Tinubu is {age(remi['birth_date'])} (born 21 September 1960). Ages are calculated from local stored birth dates as of {today}; no live lookup was used."
    else:reply=f"{fact['entity']} was born on {dt.date.fromisoformat(fact['birth_date']).strftime('%d %B %Y')} and is {a} years old as of {today}. This uses local stored knowledge, not a live lookup."
   else:reply="I don't have a reliable birth date stored for that person yet, so I won't guess their age."
  elif action in {"retrieve","followup","knowledge"}:
   if ev and ev[0]["score"]>=0.9:
    f=ev[0]["fact"]; reply=f.get("pcm" if pcm else "en") or f["en"]
   else:reply="I don't have enough reliable local information to answer that yet, and I won't invent a fact." if not pcm else "I never get enough reliable local information to answer that one yet, and I no wan invent fact."
  else:reply="I don't have enough reliable local information to answer that yet."
  check=self.validator.validate(reply,action,ev)
  if not check["ok"]:reply="I couldn't produce a sufficiently supported answer. Please try a more specific question.";source="jre_safe_fallback"
  confidence=plan["confidence"] if not ev else min(.9,.58 if ev[0]["score"]<.9 else .86)
  if action=="calculation" and tool is not None:confidence=.99
  sources=[{"title":x["fact"]["topic"],"url":"local://knowledge/"+x["fact"]["id"]} for x in ev[:3]]
  latency=int((time.perf_counter()-started)*1000)
  trace=[{"stage":"plan","action":action,"purpose":plan["purpose"]},{"stage":"retrieval","count":len(ev),"candidate_ids":[x["fact"]["id"] for x in ev[:3]]},{"stage":"validation","ok":check["ok"],"issues":check["issues"]},{"stage":"response","answered_by":source,"confidence":round(confidence,2),"latency_ms":latency}]
  return {"reply":reply,"answered_by":source,"confidence":round(confidence,2),"sources":sources,"trace":trace,"latency_ms":latency,"model_used":False}
class JarvisBrain:
 def __init__(self,store=None,kb=None):self.store=store or ConversationStore();self.kb=kb or LocalKnowledgeBase();self.understanding=UnderstandingEngine();self.planner=DecisionEngine();self.jre=JarvisResponseEngine(self.kb,self.store)
 def respond(self,session,message):
  started=time.perf_counter();sid=norm(session or "anonymous")[:120];msg=norm(message)[:2000];self.store.ensure(sid);self.store.add(sid,"user",msg)
  u=self.understanding.analyze(msg);ctx=self.store.context(sid)
  # Context excludes the current user turn for conversational reference resolution.
  prior=ctx["turns"][:-1];ctx["turns"]=prior;ctx["last_assistant"]=next((x["content"] for x in reversed(prior) if x["role"]=="assistant"),"")
  plan=self.planner.plan(u,ctx)
  if u["topic"]:
   self.store.topic(sid,u["topic"]);ctx["topic"]=u["topic"]
  out=self.jre.respond(u,plan,ctx,sid)
  trace=[{"stage":"receive","length":len(msg)},{"stage":"understanding","intent":u["intent"],"qtype":u["qtype"],"language":u["language"],"topic":u["topic"]},{"stage":"context","turns":len(prior),"topic":ctx["topic"]},{"stage":"decision","action":plan["action"]}]+out.pop("trace")
  out.update({"intent":u["intent"],"qtype":u["qtype"],"lang":u["language"],"trace":trace,"latency_ms":int((time.perf_counter()-started)*1000)})
  self.store.add(sid,"assistant",out["reply"],{"intent":out["intent"],"answered_by":out["answered_by"]})
  self.store.log("experiments",sid,{k:out[k] for k in ("intent","qtype","lang","answered_by","confidence","latency_ms")})
  return out
