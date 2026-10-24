import json
from http.server import BaseHTTPRequestHandler
from jarvis_brain import JarvisBrain
_BRAIN = None
def brain():
    global _BRAIN
    if _BRAIN is None: _BRAIN = JarvisBrain()
    return _BRAIN
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body=json.dumps({'status':'ok','service':'Naija Brain JB/JRE','external_llm':False}).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<1 or n>12000: raise ValueError()
            data=json.loads(self.rfile.read(n))
            msg=data.get('message',''); session=data.get('session','anonymous')
            if not isinstance(msg,str) or len(msg)>2000 or not isinstance(session,str): raise ValueError()
            out=brain().respond(session,msg); body=json.dumps(out,ensure_ascii=False).encode()
            self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
        except Exception:
            body=json.dumps({'error':'Invalid request or response failure'}).encode(); self.send_response(400); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass
