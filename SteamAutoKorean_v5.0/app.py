import sys,os,re,json,hashlib,ctypes,time,traceback,shutil
from ctypes import wintypes
from pathlib import Path
from PySide6 import QtCore,QtGui,QtWidgets
from PIL import ImageGrab,ImageEnhance,ImageFilter
import pytesseract
# Single-installer Windows build: use bundled Tesseract when present.
_BUNDLED_TESS = Path(__file__).resolve().parent / "tesseract" / "tesseract.exe"
if _BUNDLED_TESS.exists():
    pytesseract.pytesseract.tesseract_cmd = str(_BUNDLED_TESS)
try:
 import argostranslate.translate
 ARGOS=True
except Exception:
 ARGOS=False

BASE=Path(__file__).resolve().parent
_USER_ROOT=Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SteamAutoKorean"
DATA=_USER_ROOT/"data"; DATA.mkdir(parents=True,exist_ok=True)
PROFILES=DATA/"profiles"; PROFILES.mkdir(exist_ok=True)
_BUNDLED_DATA=BASE/"data"
for _name in ("config.json","glossary.json","translation_cache.json"):
 try:
  _dst=DATA/_name;_src=_BUNDLED_DATA/_name
  if not _dst.exists() and _src.exists(): shutil.copy2(_src,_dst)
 except Exception: pass
GLOSS=DATA/"glossary.json"
SESSION_FILE=DATA/"session_state.json"
def load(p,d):
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:
  try:
   p=Path(p)
   if p.exists():
    bad=p.with_suffix(p.suffix+f".corrupt.{int(time.time())}")
    p.replace(bad)
  except Exception: pass
  return d
def save(p,x):
 try:
  p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
  tmp=p.with_suffix(p.suffix+".tmp")
  tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf-8")
  tmp.replace(p)
 except Exception:
  pass
gloss=load(GLOSS,{})
SYSTEMS=["PC / Steam","FC/NES","SFC/SNES","Mega Drive/Genesis","GB/GBC/GBA","Nintendo 64","Nintendo DS","Nintendo 3DS","PS1","PS2","PS3","PSP","Sega Saturn/SS","Dreamcast","GameCube/Wii","Xbox","Xbox 360","Switch","RetroArch","기타"]

def windows():
 if sys.platform!="win32": return []
 u=ctypes.windll.user32; out=[]
 CB=ctypes.WINFUNCTYPE(ctypes.c_bool,wintypes.HWND,wintypes.LPARAM)
 def cb(h,l):
  if u.IsWindowVisible(h) and u.GetWindowTextLengthW(h)>0:
   n=u.GetWindowTextLengthW(h)+1;b=ctypes.create_unicode_buffer(n);u.GetWindowTextW(h,b,n)
   r=wintypes.RECT()
   if u.GetWindowRect(h,ctypes.byref(r)):
    w,hg=r.right-r.left,r.bottom-r.top
    if w>300 and hg>200: out.append((int(h),b.value,(r.left,r.top,w,hg)))
  return True
 u.EnumWindows(CB(cb),0); return out
def rect(hwnd):
 if sys.platform!="win32":return None
 r=wintypes.RECT()
 if ctypes.windll.user32.GetWindowRect(hwnd,ctypes.byref(r)):return (r.left,r.top,r.right-r.left,r.bottom-r.top)
def monitor_rect_for_window(hwnd):
 if sys.platform!="win32":return None
 try:
  u=ctypes.windll.user32
  MONITOR_DEFAULTTONEAREST=2
  mon=u.MonitorFromWindow(hwnd,MONITOR_DEFAULTTONEAREST)
  class MI(ctypes.Structure):
   _fields_=[("cbSize",wintypes.DWORD),("rcMonitor",wintypes.RECT),("rcWork",wintypes.RECT),("dwFlags",wintypes.DWORD)]
  mi=MI();mi.cbSize=ctypes.sizeof(MI)
  ctypes.windll.user32.GetMonitorInfoW(mon,ctypes.byref(mi))
  r=mi.rcMonitor;return (r.left,r.top,r.right-r.left,r.bottom-r.top)
 except:return None
def display_mode(hwnd):
 wr=rect(hwnd);mr=monitor_rect_for_window(hwnd)
 if not wr:return "알 수 없음"
 if mr:
  wx,wy,ww,wh=wr;mx,my,mw,mh=mr
  if abs(wx-mx)<=3 and abs(wy-my)<=3 and abs(ww-mw)<=6 and abs(wh-mh)<=6:
   return "전체화면/무테두리 전체화면"
 return "창모드"
def virtual_screen():
 if sys.platform!="win32":return (0,0,1920,1080)
 u=ctypes.windll.user32
 return (u.GetSystemMetrics(76),u.GetSystemMetrics(77),u.GetSystemMetrics(78),u.GetSystemMetrics(79))
LANG_NAMES={"ja":"일본어","en":"영어","zh":"중국어","es":"스페인어","fr":"프랑스어","de":"독일어","it":"이탈리아어","pt":"포르투갈어","ru":"러시아어","th":"태국어","vi":"베트남어","id":"인도네시아어","tr":"터키어","pl":"폴란드어","nl":"네덜란드어"}
def detect_language(text):
 if re.search(r"[ぁ-んァ-ン]",text):return "ja"
 if re.search(r"[一-龯]",text):return "zh"
 if re.search(r"[А-Яа-яЁё]",text):return "ru"
 if re.search(r"[ก-๙]",text):return "th"
 if re.search(r"[ăâđêôơưĂÂĐÊÔƠƯ]",text):return "vi"
 low=" "+text.lower()+" "
 scores={
  "es":sum(x in low for x in [" el "," la "," que "," para "," una ","ción"]),
  "fr":sum(x in low for x in [" le "," la "," de "," que "," pour "," une ","é"]),
  "de":sum(x in low for x in [" der "," die "," das "," und "," für "," nicht "]),
  "it":sum(x in low for x in [" il "," la "," che "," per "," una ","zione"]),
  "pt":sum(x in low for x in [" o "," a "," que "," para "," uma ","ção"]),
  "id":sum(x in low for x in [" yang "," dan "," untuk "," tidak "," dengan "]),
  "tr":sum(x in low for x in [" ve "," bir "," için "," değil "," ile "]),
  "pl":sum(x in low for x in [" i "," nie "," jest "," dla "," się "," że "]),
  "nl":sum(x in low for x in [" de "," het "," een "," niet "," voor "," van "]),
  "vi":sum(x in low for x in [" và "," không "," một "," cho "," của "])
 }
 best=max(scores,key=scores.get)
 return best if scores[best]>=2 else "en"
def norm(t):return " ".join(t.split()).strip()
def skey(t):return re.sub(r"[\s\W_]+","",t,flags=re.UNICODE).lower()
def pname(title):return re.sub(r'[<>:"/\\|?*]+','_',title)[:80] or "default"

class Overlay(QtWidgets.QWidget):
 def __init__(self):
  super().__init__();self.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.Tool|QtCore.Qt.WindowTransparentForInput);self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
  self.l=QtWidgets.QLabel(self);self.l.setWordWrap(True);self.l.setAlignment(QtCore.Qt.AlignCenter);self.l.setStyleSheet("color:white;background:rgba(0,0,0,180);padding:10px;font-weight:700;border-radius:10px")
 def showtext(self,t,r):
  x,y,w,h=r;oh=max(90,min(220,h));self.setGeometry(x,y+h-oh,w,oh);self.l.setGeometry(0,0,w,oh);f=self.l.font();f.setPointSize(22);self.l.setFont(f);self.l.setText(t);self.show()

class FullScreenOverlay(QtWidgets.QWidget):
 def __init__(self):
  super().__init__();self.items=[]
  self.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.Tool|QtCore.Qt.WindowTransparentForInput)
  self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
 def set_items(self,items,window_rect):
  self.items=items; x,y,w,h=window_rect; self.setGeometry(x,y,w,h); self.show(); self.update()
 def paintEvent(self,e):
  p=QtGui.QPainter(self);p.setRenderHint(QtGui.QPainter.Antialiasing)
  for item in self.items:
   x,y,w,h,text,*rest=item
   r=QtCore.QRect(x,y,w,h)
   bg=rest[0] if rest else (0,0,0)
   p.fillRect(r,QtGui.QColor(int(bg[0]),int(bg[1]),int(bg[2]),245))
   f=QtGui.QFont();f.setPointSize(max(10,min(28,int(h*0.48))));f.setBold(True);p.setFont(f)
   # Choose white/black Korean from estimated background luminance, with opposite outline.
   lum=0.2126*bg[0]+0.7152*bg[1]+0.0722*bg[2]
   fg=QtGui.QColor(255,255,255) if lum<145 else QtGui.QColor(20,20,20)
   ol=QtGui.QColor(0,0,0) if lum<145 else QtGui.QColor(255,255,255)
   rr=r.adjusted(4,2,-4,-2)
   p.setPen(ol)
   for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
    p.drawText(rr.translated(dx,dy),QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter|QtCore.Qt.TextWordWrap,text)
   p.setPen(fg);p.drawText(rr,QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter|QtCore.Qt.TextWordWrap,text)

class Selector(QtWidgets.QWidget):
 picked=QtCore.Signal(tuple)
 def __init__(self):
  super().__init__();self.a=self.b=None;self.setWindowFlags(QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint);self.setWindowState(QtCore.Qt.WindowFullScreen);self.setAttribute(QtCore.Qt.WA_TranslucentBackground);self.setCursor(QtCore.Qt.CrossCursor)
 def mousePressEvent(self,e):self.a=e.position().toPoint();self.b=self.a
 def mouseMoveEvent(self,e):self.b=e.position().toPoint();self.update()
 def mouseReleaseEvent(self,e):
  self.b=e.position().toPoint();r=QtCore.QRect(self.a,self.b).normalized();self.picked.emit((r.x(),r.y(),r.width(),r.height()));self.close()
 def paintEvent(self,e):
  p=QtGui.QPainter(self);p.fillRect(self.rect(),QtGui.QColor(0,0,0,80))
  if self.a and self.b:
   r=QtCore.QRect(self.a,self.b).normalized();p.setCompositionMode(QtGui.QPainter.CompositionMode_Clear);p.fillRect(r,QtCore.Qt.transparent)

class Main(QtWidgets.QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle("Steam Auto Korean v2.0 - Windows / Android");self.resize(820,560);self.ov=Overlay();self.fullov=FullScreenOverlay();self.hwnd=None
  self.history=[];self.learned={};self.game_terms={};self.ui_memory={};self.timeline=[];self.safe_mode=False;self.genre='자동';self.busy=False;self.capture_errors=0;self.last_error_time=0;self.adaptive_ms=900;self.proc_avg=0.0;self.last_frame_sig=None;self.pending_text='';self.pending_hits=0;self.last_overlay_time=0.0;self.busy_since=0.0;self.last_maintenance=time.time();self.last_src="";self.last_out="";self.last_conf=0;self.wrect=None;self.rel=None;self.last="";self.cache={};self.running=False
  w=QtWidgets.QWidget();self.setCentralWidget(w);v=QtWidgets.QVBoxLayout(w)
  t=QtWidgets.QLabel("🎮 Steam Auto Korean v2.0");f=t.font();f.setPointSize(19);f.setBold(True);t.setFont(f);v.addWidget(t)
  v.addWidget(QtWidgets.QLabel("실행 중인 게임/에뮬레이터 창을 선택하면 창 이동·크기 변경을 따라 OCR 영역을 추적합니다."))
  form=QtWidgets.QFormLayout();self.system=QtWidgets.QComboBox();self.system.addItems(SYSTEMS);form.addRow("기종",self.system)
  self.genreBox=QtWidgets.QComboBox();self.genreBox.addItems(["자동","RPG / 비주얼노벨","액션 / 아케이드","전략 / 시뮬레이션","어드벤처 / 퍼즐"]);self.genreBox.currentTextChanged.connect(self.apply_genre_profile);form.addRow("게임 장르",self.genreBox)
  self.mode=QtWidgets.QComboBox();self.mode.addItems(["기존 자막 모드","전체 화면 원문 교체"]);form.addRow("표시 모드",self.mode)
  self.bgmode=QtWidgets.QComboBox();self.bgmode.addItems(["주변색 자동 복원","검정 가림"]);form.addRow("원문 지우기",self.bgmode)
  self.capturemode=QtWidgets.QComboBox();self.capturemode.addItems(["자동 (권장)","창 영역 추적","모니터 전체"]);form.addRow("화면 캡처",self.capturemode)
  self.disp=QtWidgets.QLabel("미연결");form.addRow("감지된 표시 방식",self.disp)
  wh=QtWidgets.QHBoxLayout();self.win=QtWidgets.QComboBox();wh.addWidget(self.win,1);rb=QtWidgets.QPushButton("창 새로고침");rb.clicked.connect(self.refresh);wh.addWidget(rb);form.addRow("게임 창",wh);v.addLayout(form)
  h=QtWidgets.QHBoxLayout()
  b=QtWidgets.QPushButton("게임 자동 찾기");b.clicked.connect(lambda:(self.refresh(),self.auto_select_game()));h.addWidget(b)
  b=QtWidgets.QPushButton("창 연결");b.clicked.connect(self.attach);h.addWidget(b)
  b=QtWidgets.QPushButton("자동 대화영역 후보");b.clicked.connect(self.auto_region);h.addWidget(b)
  b=QtWidgets.QPushButton("F9 영역 보정");b.clicked.connect(self.select);h.addWidget(b)
  b=QtWidgets.QPushButton("F8 시작/중지");b.clicked.connect(self.toggle);h.addWidget(b);v.addLayout(h)
  ah=QtWidgets.QHBoxLayout()
  b=QtWidgets.QPushButton("번역 수정/학습");b.clicked.connect(self.learn_translation);ah.addWidget(b)
  b=QtWidgets.QPushButton("문맥 기록 보기");b.clicked.connect(self.show_history);ah.addWidget(b)
  b=QtWidgets.QPushButton("문맥 초기화");b.clicked.connect(self.clear_history);ah.addWidget(b)
  b=QtWidgets.QPushButton("📚 게임 자동 사전");b.clicked.connect(self.show_dictionary);ah.addWidget(b)
  b=QtWidgets.QPushButton("🧩 UI 위치 기억");b.clicked.connect(self.show_ui_memory);ah.addWidget(b)
  b=QtWidgets.QPushButton("⏪ 번역 타임머신");b.clicked.connect(self.show_timeline);ah.addWidget(b)
  b=QtWidgets.QPushButton("🧰 진단 리포트");b.clicked.connect(self.export_diagnostics);ah.addWidget(b)
  b=QtWidgets.QPushButton("💾 사용자 데이터 백업");b.clicked.connect(self.backup_user_data);ah.addWidget(b)
  b=QtWidgets.QPushButton("↩ 백업 복원");b.clicked.connect(self.restore_user_data);ah.addWidget(b);v.addLayout(ah)
  self.status=QtWidgets.QPlainTextEdit();self.status.setReadOnly(True);v.addWidget(self.status)
  self.timer=QtCore.QTimer(self);self.timer.timeout.connect(self.capture)
  QtGui.QShortcut(QtGui.QKeySequence("F8"),self).activated.connect(self.toggle);QtGui.QShortcut(QtGui.QKeySequence("F9"),self).activated.connect(self.select)
  self.refresh()
  self.check_previous_session()
  self.mark_session(True)
 def recommend_profile(self,title):
  low=title.lower()
  system="PC / Steam";genre="자동"
  emu=[
   (("duckstation","ps1"),"DuckStation (PS1)"),
   (("pcsx2","ps2"),"PCSX2 (PS2)"),
   (("rpcs3","ps3"),"RPCS3 (PS3)"),
   (("ppsspp","psp"),"PPSSPP (PSP)"),
   (("retroarch",),"RetroArch"),
   (("dolphin",),"Dolphin"),
   (("snes9x","bsnes"),"SFC/SNES"),
   (("mgba","sameboy"),"GB/GBC/GBA"),
   (("xenia",),"Xbox 360"),
   (("xemu",),"Xbox")
  ]
  for keys,name in emu:
   if any(k in low for k in keys):system=name;break
  if any(k in low for k in ("rpg","final fantasy","dragon quest","persona","tales")):genre="RPG / 비주얼노벨"
  elif any(k in low for k in ("fighter","arcade","action","shoot","racing")):genre="액션 / 아케이드"
  elif any(k in low for k in ("strategy","simulation","simulator","civilization")):genre="전략 / 시뮬레이션"
  return system,genre
 def auto_select_game(self):
  # Prefer the largest visible non-self window as a conservative first candidate.
  candidates=[x for x in getattr(self,"ws",[]) if "Steam Auto Korean" not in x[1]]
  if not candidates:return
  h,t,r=max(candidates,key=lambda x:x[2][2]*x[2][3])
  for i in range(self.win.count()):
   if int(self.win.itemData(i))==int(h):
    self.win.setCurrentIndex(i);break
  pf=PROFILES/(pname(t)+".json")
  if not pf.exists():
   sysname,genre=self.recommend_profile(t)
   try:
    self.system.setCurrentText(sysname)
    if hasattr(self,"genreBox"):self.genreBox.setCurrentText(genre)
   except Exception:pass
   self.status.appendPlainText(f"새 게임 후보: {t} / 추천 {sysname}, {genre}")
 def refresh(self):
  self.win.clear();self.ws=windows()
  for h,t,r in self.ws:self.win.addItem(t,h)
  self.status.appendPlainText(f"표시 가능한 창 {len(self.ws)}개 검색")
  if not self.hwnd:self.auto_select_game()
 def attach(self):
  if self.win.currentIndex()<0:return
  self.hwnd=int(self.win.currentData());self.wrect=rect(self.hwnd);title=self.win.currentText();self.disp.setText(display_mode(self.hwnd));pf=PROFILES/(pname(title)+".json")
  d=load(pf,{})
  self.rel=d.get("relative_region")
  try:
   if d.get("system"):self.system.setCurrentText(d["system"])
   if hasattr(self,"genreBox") and d.get("genre"):self.genreBox.setCurrentText(d["genre"])
   if hasattr(self,"mode") and d.get("display_mode"):self.mode.setCurrentText(d["display_mode"])
   if hasattr(self,"capturemode") and d.get("capture_mode"):self.capturemode.setCurrentText(d["capture_mode"])
   if hasattr(self,"bgmode") and d.get("background_mode"):self.bgmode.setCurrentText(d["background_mode"])
  except Exception as e:self.log_error("profile_restore",e)
  self.cache=load(PROFILES/(pname(title)+"_cache.json"),{})
  self.learned=load(PROFILES/(pname(title)+"_learned.json"),{})
  self.history=load(PROFILES/(pname(title)+"_history.json"),[])
  self.game_terms=load(PROFILES/(pname(title)+"_terms.json"),{})
  self.ui_memory=load(PROFILES/(pname(title)+"_ui_memory.json"),{})
  self.timeline=load(PROFILES/(pname(title)+"_timeline.json"),[])
  self.status.appendPlainText("연결: "+title+(" / 저장 프로필 불러옴" if self.rel else ""))
 def auto_region(self):
  if not self.hwnd:self.attach()
  r=rect(self.hwnd) if self.hwnd else None
  if not r:return
  # Conservative candidate: lower 38% of the selected game window, common dialogue/subtitle zone.
  self.rel=[0.05,0.58,0.90,0.37];self.save_profile();self.status.appendPlainText("하단 대화영역 후보를 설정했습니다. F9로 정확히 보정할 수 있습니다.")
 def select(self):
  if not self.hwnd:self.attach()
  self.timer.stop();self.ov.hide();self.fullov.hide();x=Selector();x.picked.connect(self.selected);self.sel=x;x.show()
 def selected(self,a):
  wr=(monitor_rect_for_window(self.hwnd) if self.capturemode.currentIndex()==2 else rect(self.hwnd)) if self.hwnd else None
  if not wr:return
  x,y,w,h=a;wx,wy,ww,wh=wr
  self.rel=[(x-wx)/ww,(y-wy)/wh,w/ww,h/wh];self.save_profile();self.status.appendPlainText("창 상대좌표로 OCR 영역 저장 완료")
 def history_path(self):
  return PROFILES/(pname(self.win.currentText())+"_history.json")
 def learned_path(self):
  return PROFILES/(pname(self.win.currentText())+"_learned.json")
 def remember(self,src,out,conf=0):
  if not src or not out:return
  if self.history and self.history[-1].get("source")==src:return
  self.history.append({"source":src,"ko":out,"confidence":round(float(conf),1)})
  self.history=self.history[-80:];save(self.history_path(),self.history)
 def learn_translation(self):
  if not self.last_src:return
  text,ok=QtWidgets.QInputDialog.getMultiLineText(self,"번역 수정/학습","이 문장의 한국어 번역을 수정하면 이 게임에서 다음부터 그대로 사용합니다.",self.last_out)
  if ok and text.strip():
   self.learned[self.last_src]=text.strip();save(self.learned_path(),self.learned)
   hs=hashlib.sha1(self.last_src.encode()).hexdigest();self.cache[hs]=text.strip()
   save(PROFILES/(pname(self.win.currentText())+"_cache.json"),self.cache)
   self.last_out=text.strip();self.status.appendPlainText("\n✓ 사용자 번역을 학습했습니다.")
 def show_history(self):
  dlg=QtWidgets.QDialog(self);dlg.setWindowTitle("게임 문맥 기록");dlg.resize(700,500);v=QtWidgets.QVBoxLayout(dlg);q=QtWidgets.QPlainTextEdit();q.setReadOnly(True)
  q.setPlainText("\n\n".join(f'{i+1}. {x.get("source","")}\n→ {x.get("ko","")}' for i,x in enumerate(self.history[-40:])))
  v.addWidget(q);dlg.exec()
 def clear_history(self):
  self.history=[];save(self.history_path(),[]);self.status.appendPlainText("문맥 기록을 초기화했습니다.")
 def watchdog(self):
  if self.busy and self.busy_since and time.time()-self.busy_since>12:
   self.log_error("watchdog",RuntimeError("OCR busy > 12s; forced reset"))
   self.busy=False;self.busy_since=0
 def maintenance(self):
  now=time.time()
  if now-self.last_maintenance<300:return
  self.last_maintenance=now
  try:
   if len(self.history)>80:self.history=self.history[-80:]
   if len(self.timeline)>300:self.timeline=self.timeline[-300:]
   self.trim_cache()
  except Exception as e:self.log_error("maintenance",e)
 def stable_text(self,text):
  key=skey(text)
  if not key:return False
  if key==self.pending_text:self.pending_hits+=1
  else:self.pending_text=key;self.pending_hits=1
  return self.pending_hits>=self.genre_stable_hits()
 def expire_overlay(self):
  if self.last_overlay_time and time.time()-self.last_overlay_time>self.genre_overlay_ttl():
   try:self.ov.hide();self.fullov.hide()
   except Exception:pass
   self.last_overlay_time=0
 def apply_genre_profile(self,name):
  self.genre=name
  if name=="RPG / 비주얼노벨":
   self.adaptive_ms=max(self.adaptive_ms,1000)
  elif name=="액션 / 아케이드":
   self.adaptive_ms=700
  elif name=="전략 / 시뮬레이션":
   self.adaptive_ms=max(self.adaptive_ms,1200)
  elif name=="어드벤처 / 퍼즐":
   self.adaptive_ms=max(self.adaptive_ms,900)
  if self.running:self.timer.setInterval(self.adaptive_ms)
 def genre_stable_hits(self):
  return 2 if self.genre in ("자동","RPG / 비주얼노벨","전략 / 시뮬레이션") else 1
 def genre_overlay_ttl(self):
  if self.genre=="전략 / 시뮬레이션":return 12
  if self.genre=="액션 / 아케이드":return 5
  return 8
 def frame_signature(self,img):
  try:
   small=img.convert("L").resize((32,18))
   px=list(small.getdata());avg=sum(px)/max(1,len(px))
   return tuple(1 if p>=avg else 0 for p in px)
  except Exception:return None
 def frame_changed(self,sig):
  if sig is None:return True
  old=self.last_frame_sig;self.last_frame_sig=sig
  if old is None or len(old)!=len(sig):return True
  diff=sum(1 for a,b in zip(old,sig) if a!=b)/len(sig)
  return diff>=0.025
 def adapt_interval(self,elapsed):
  self.proc_avg=elapsed if self.proc_avg<=0 else self.proc_avg*0.8+elapsed*0.2
  target=int(max(650,min(2500,self.proc_avg*1800+550)))
  self.adaptive_ms=int(self.adaptive_ms*0.75+target*0.25)
  if self.running:self.timer.setInterval(self.adaptive_ms)
 def backup_user_data(self):
  try:
   b=DATA/"backup";b.mkdir(exist_ok=True)
   # User-authored/learned data only; caches can be regenerated.
   for p in PROFILES.glob("*_learned.json"):
    shutil.copy2(p,b/p.name)
   for p in PROFILES.glob("*_terms.json"):
    shutil.copy2(p,b/p.name)
   if GLOSS.exists():shutil.copy2(GLOSS,b/GLOSS.name)
   save(b/"backup_meta.json",{"time":time.time(),"version":"3.3"})
   self.status.appendPlainText("사용자 번역/사전 백업 완료")
  except Exception as e:self.log_error("backup",e)
 def restore_user_data(self):
  try:
   b=DATA/"backup"
   if not b.exists():return
   for p in b.glob("*_learned.json"):shutil.copy2(p,PROFILES/p.name)
   for p in b.glob("*_terms.json"):shutil.copy2(p,PROFILES/p.name)
   if (b/GLOSS.name).exists():shutil.copy2(b/GLOSS.name,GLOSS)
   self.status.appendPlainText("백업에서 사용자 번역/사전을 복원했습니다.")
  except Exception as e:self.log_error("restore",e)
 def mark_session(self,running):
  save(SESSION_FILE,{"running":bool(running),"time":time.time(),"version":"3.0"})
 def check_previous_session(self):
  st=load(SESSION_FILE,{})
  if st.get("running"):
   self.safe_mode=True;self.adaptive_ms=max(self.adaptive_ms,1600)
   self.status.appendPlainText("이전 실행이 정상 종료되지 않았습니다. 안전모드: OCR 간격을 낮춰 시작합니다.")
 def export_diagnostics(self):
  try:
   p=DATA/"diagnostic_export.txt"
   lines=["Steam Auto Korean v3.0 Diagnostics",f"time={time.strftime('%Y-%m-%d %H:%M:%S')}",f"safe_mode={self.safe_mode}",f"adaptive_ms={self.adaptive_ms}",f"capture_errors={self.capture_errors}"]
   dp=self.diagnostic_path()
   if dp.exists():lines+=["","--- recent log ---"]+dp.read_text(encoding="utf-8",errors="replace").splitlines()[-150:]
   p.write_text("\n".join(lines),encoding="utf-8")
   self.status.appendPlainText("진단 리포트 저장: "+str(p))
  except Exception as e:self.log_error("export",e)
 def diagnostic_path(self):
  return DATA/"diagnostic.log"
 def log_error(self,where,e):
  try:
   with self.diagnostic_path().open("a",encoding="utf-8") as f:
    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {where}: {type(e).__name__}: {e}\n")
  except Exception:pass
 def recover_capture(self):
  self.capture_errors+=1;self.last_error_time=time.time()
  if self.capture_errors>=5:
   self.timer.stop();self.running=False;self.busy=False;self.ov.hide();self.fullov.hide()
   self.status.appendPlainText("연속 캡처 오류 5회로 자동 중지했습니다. 게임 창을 다시 연결한 뒤 시작하세요.")
 def timeline_path(self):
  return PROFILES/(pname(self.win.currentText())+"_timeline.json")
 def add_timeline(self,src,ko,conf=0,slot="dialog"):
  if not src or not ko:return
  if self.timeline and self.timeline[-1].get("source")==src:return
  self.timeline.append({"time":time.strftime("%H:%M:%S"),"source":src,"ko":ko,"confidence":round(float(conf),1),"slot":slot})
  self.timeline=self.timeline[-300:];save(self.timeline_path(),self.timeline)
 def show_timeline(self):
  dlg=QtWidgets.QDialog(self);dlg.setWindowTitle("⏪ 번역 타임머신");dlg.resize(820,580);v=QtWidgets.QVBoxLayout(dlg)
  q=QtWidgets.QPlainTextEdit();q.setReadOnly(True)
  q.setPlainText("\n\n".join(f'[{e.get("time","--:--:--")}]  신뢰도 {e.get("confidence",0)}%\n{e.get("source","")}\n→ {e.get("ko","")}' for e in self.timeline[-150:]))
  v.addWidget(q);h=QtWidgets.QHBoxLayout();copy=QtWidgets.QPushButton("전체 기록 클립보드 복사");clear=QtWidgets.QPushButton("기록 초기화");h.addWidget(copy);h.addWidget(clear);v.addLayout(h)
  copy.clicked.connect(lambda:QtWidgets.QApplication.clipboard().setText(q.toPlainText()))
  def wipe():
   self.timeline=[];save(self.timeline_path(),[]);q.clear();self.status.appendPlainText("번역 타임머신 기록을 초기화했습니다.")
  clear.clicked.connect(wipe);dlg.exec()
 def auto_promote_terms(self):
  # Repeated candidates become visible dictionary entries automatically; never invent a Korean translation.
  changed=False
  for term,e in list(self.game_terms.items()):
   if int(e.get("count",0))>=5 and not e.get("promoted"):
    e["promoted"]=True;changed=True
  if changed:save(self.terms_path(),self.game_terms)
 def ui_memory_path(self):
  return PROFILES/(pname(self.win.currentText())+"_ui_memory.json")
 def ui_key(self,x,y,w,h,ww,wh):
  # Quantize to a 20x12 grid so small OCR box jitter still hits the same UI slot.
  cx=(x+w/2)/max(1,ww);cy=(y+h/2)/max(1,wh)
  return f"{round(cx*20)}/{round(cy*12)}"
 def remember_ui(self,key,src,ko,conf):
  if conf<35:return
  e=self.ui_memory.get(key)
  if not e or conf>=float(e.get("confidence",0))-5:
   self.ui_memory[key]={"source":src,"ko":ko,"confidence":round(float(conf),1),"hits":int((e or {}).get("hits",0))+1}
   save(self.ui_memory_path(),self.ui_memory)
 def ui_translation(self,key,src,conf):
  e=self.ui_memory.get(key)
  if not e:return None
  old=e.get("source","")
  # Exact/near-identical OCR at same screen slot can reuse stable Korean.
  a=skey(old);b=skey(src)
  if a==b:return e.get("ko")
  if a and b:
   common=sum(1 for x,y in zip(a,b) if x==y)/max(len(a),len(b))
   if common>=0.82 and conf<70:return e.get("ko")
  return None
 def show_ui_memory(self):
  dlg=QtWidgets.QDialog(self);dlg.setWindowTitle("UI 위치 기억");dlg.resize(760,500);v=QtWidgets.QVBoxLayout(dlg)
  q=QtWidgets.QPlainTextEdit();q.setReadOnly(True)
  rows=sorted(self.ui_memory.items(),key=lambda x:int(x[1].get("hits",0)),reverse=True)
  q.setPlainText("\n\n".join(f'위치 {k} · {e.get("hits",0)}회 · 신뢰도 {e.get("confidence",0)}%\n{e.get("source","")} → {e.get("ko","")}' for k,e in rows[:100]))
  v.addWidget(q);b=QtWidgets.QPushButton("UI 위치 기억 전체 초기화")
  def clear():
   self.ui_memory={};save(self.ui_memory_path(),{});q.clear();self.status.appendPlainText("UI 위치 기억을 초기화했습니다.")
  b.clicked.connect(clear);v.addWidget(b);dlg.exec()
 def terms_path(self):
  return PROFILES/(pname(self.win.currentText())+"_terms.json")
 def collect_terms(self,text):
  for term in self.extract_terms(text):
   e=self.game_terms.setdefault(term,{"ko":"","count":0})
   e["count"]=int(e.get("count",0))+1
  save(self.terms_path(),self.game_terms);self.auto_promote_terms()
 def apply_game_terms(self,text):
  # Longest first prevents a short term from corrupting a longer fixed name.
  for src,e in sorted(self.game_terms.items(),key=lambda x:len(x[0]),reverse=True):
   ko=e.get("ko","") if isinstance(e,dict) else ""
   if ko:text=text.replace(src,ko)
  return text
 def show_dictionary(self):
  dlg=QtWidgets.QDialog(self);dlg.setWindowTitle("게임 자동 사전");dlg.resize(760,520);v=QtWidgets.QVBoxLayout(dlg)
  table=QtWidgets.QTableWidget();table.setColumnCount(3);table.setHorizontalHeaderLabels(["원문 용어","확정 한국어","출현"]);table.horizontalHeader().setStretchLastSection(False);table.horizontalHeader().setSectionResizeMode(0,QtWidgets.QHeaderView.Stretch);table.horizontalHeader().setSectionResizeMode(1,QtWidgets.QHeaderView.Stretch)
  rows=sorted(self.game_terms.items(),key=lambda x:int(x[1].get("count",0)),reverse=True);table.setRowCount(len(rows))
  for r,(term,e) in enumerate(rows):
   table.setItem(r,0,QtWidgets.QTableWidgetItem(term));table.setItem(r,1,QtWidgets.QTableWidgetItem(e.get("ko","")));table.setItem(r,2,QtWidgets.QTableWidgetItem(str(e.get("count",0))))
  v.addWidget(table);h=QtWidgets.QHBoxLayout();sv=QtWidgets.QPushButton("확정 번역 저장");rm=QtWidgets.QPushButton("선택 후보 삭제");h.addWidget(sv);h.addWidget(rm);v.addLayout(h)
  def store():
   new={}
   for r in range(table.rowCount()):
    a=table.item(r,0);b=table.item(r,1);c=table.item(r,2)
    if a and a.text().strip():new[a.text().strip()]={"ko":b.text().strip() if b else "","count":int(c.text()) if c and c.text().isdigit() else 1}
   self.game_terms=new;save(self.terms_path(),new);self.status.appendPlainText("게임 자동 사전을 저장했습니다.")
  def remove():
   for r in sorted({i.row() for i in table.selectedIndexes()},reverse=True):table.removeRow(r)
  sv.clicked.connect(store);rm.clicked.connect(remove);dlg.finished.connect(lambda _:store());dlg.exec()
 def extract_terms(self,text):
  # Conservative candidate extraction: quoted/capitalized English terms and Japanese katakana names.
  terms=[]
  terms += re.findall(r"\b[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,})?\b",text)
  terms += re.findall(r"[ァ-ヴー]{3,}",text)
  # CJK sequences can be Chinese or Japanese kanji; keep as terminology candidates only.
  terms += re.findall(r"[一-龯]{2,8}",text)
  return list(dict.fromkeys(terms))[:10]
 def save_profile(self):
  if not self.hwnd:return
  title=self.win.currentText();save(PROFILES/(pname(title)+".json"),{
   "title":title,
   "system":self.system.currentText(),
   "relative_region":self.rel,
   "genre":self.genreBox.currentText() if hasattr(self,"genreBox") else getattr(self,"genre","자동"),
   "display_mode":self.mode.currentText() if hasattr(self,"mode") else "",
   "capture_mode":self.capturemode.currentText() if hasattr(self,"capturemode") else "",
   "background_mode":self.bgmode.currentText() if hasattr(self,"bgmode") else ""
  })
 def absregion(self):
  if not self.hwnd or not self.rel:return None
  # Monitor mode is useful for borderless/exclusive-like presentations and multi-monitor setups.
  if self.capturemode.currentIndex()==2:
   r=monitor_rect_for_window(self.hwnd)
  else:
   r=rect(self.hwnd)
  if not r:return None
  x,y,w,h=r;a,b,c,d=self.rel
  return (int(x+a*w),int(y+b*h),max(1,int(c*w)),max(1,int(d*h)))
 def translate(self,t):
  t=self.apply_game_terms(t)
  for a,b in gloss.items():t=t.replace(a,b)
  if not ARGOS:return "[로컬 번역 엔진/모델 확인] "+t
  src="ja" if re.search(r"[ぁ-んァ-ン一-龯]",t) else "en"
  try:
   L=argostranslate.translate.get_installed_languages();sl=next(x for x in L if x.code==src);ko=next(x for x in L if x.code=="ko");return sl.get_translation(ko).translate(t)
  except Exception:return "[번역 모델 확인] "+t
 def toggle(self):
  if not self.hwnd:self.attach()
  if not self.rel:self.auto_region()
  self.running=not self.running
  if self.running:self.timer.start(self.adaptive_ms);self.capture()
  else:self.timer.stop();self.ov.hide();self.fullov.hide()
 def estimate_bg(self,img,l,t,r,b):
  if self.bgmode.currentIndex()==1:return (0,0,0)
  # Sample a thin ring just outside OCR text box; median is robust to text/edges.
  rgb=img.convert("RGB");W,H=rgb.size;pts=[]
  pad=4
  for xx in range(max(0,l-pad),min(W,r+pad)):
   for yy in (max(0,t-pad),min(H-1,b+pad)):
    pts.append(rgb.getpixel((xx,yy)))
  for yy in range(max(0,t-pad),min(H,b+pad)):
   for xx in (max(0,l-pad),min(W-1,r+pad)):
    pts.append(rgb.getpixel((xx,yy)))
  if not pts:return (0,0,0)
  pts.sort(key=lambda c:c[0]+c[1]+c[2]);return pts[len(pts)//2]
 def trim_cache(self):
  if len(self.cache)>5000:
   # Keep newest insertion-order entries on modern Python dicts.
   self.cache=dict(list(self.cache.items())[-4000:])
   save(PROFILES/(pname(self.win.currentText())+"_cache.json"),self.cache)
 def translate_cached(self,t):
  if t in self.learned:out=self.learned[t]
  else:
   hs=hashlib.sha1(t.encode()).hexdigest();out=self.cache.get(hs)
   if not out:
    out=self.translate(t);self.cache[hs]=out;save(PROFILES/(pname(self.win.currentText())+"_cache.json"),self.cache);self.trim_cache()
  self.last_src=t;self.last_out=out
  return out
 def capture(self):
  self.watchdog();self.maintenance();self.expire_overlay()
  if self.busy:return
  self.busy=True;self.busy_since=time.time()
  ar=self.absregion()
  if not ar:
   self.busy=False;return
  if not ar:return
  x,y,w,h=ar
  if w<2 or h<2:
   self.busy=False;return
  started=time.perf_counter()
  try:
   im=ImageGrab.grab(bbox=(x,y,x+w,y+h),all_screens=True)
   self.capture_errors=0
   sig=self.frame_signature(im)
   if not self.frame_changed(sig):
    self.busy=False;return
   if self.mode.currentIndex()==0:
    g=ImageEnhance.Contrast(im.convert("L")).enhance(1.9);g=g.filter(ImageFilter.SHARPEN)
    t=norm(pytesseract.image_to_string(g,lang="jpn+eng+chi_sim+chi_tra+spa+fra+deu+ita+por+rus+tha+vie+ind+tur+pol+nld",config="--psm 6"))
    if len(t)<2:return
    k=skey(t)
    if k==self.last:return
    if not self.stable_text(t):return
    self.last=k;out=self.translate_cached(t);self.last_overlay_time=time.time()
    # OCR confidence estimate for the current region.
    cd=pytesseract.image_to_data(g,lang="jpn+eng+chi_sim+chi_tra+spa+fra+deu+ita+por+rus+tha+vie+ind+tur+pol+nld",config="--psm 6",output_type=pytesseract.Output.DICT)
    vals=[]
    for q in cd.get("conf",[]):
     try:
      q=float(q)
      if q>=0:vals.append(q)
     except:pass
    conf=sum(vals)/len(vals) if vals else 0
    self.last_conf=conf;self.remember(t,out,conf);self.add_timeline(t,out,conf,"dialog")
    self.collect_terms(t)
    terms=self.extract_terms(t)
    extra=("\n\n용어 후보: "+", ".join(terms)) if terms else ""
    lang=detect_language(t)
    self.status.setPlainText(f"감지 언어: {LANG_NAMES.get(lang,lang)} | OCR 신뢰도: {conf:.0f}%\n\n원문:\n"+t+"\n\n한국어:\n"+out+extra);self.ov.showtext(out,ar);self.fullov.hide()
   else:
    # Detect multiple text regions with Tesseract TSV.
    g=ImageEnhance.Contrast(im.convert("L")).enhance(1.8);g=g.filter(ImageFilter.SHARPEN)
    d=pytesseract.image_to_data(g,lang="jpn+eng+chi_sim+chi_tra+spa+fra+deu+ita+por+rus+tha+vie+ind+tur+pol+nld",config="--psm 11",output_type=pytesseract.Output.DICT)
    groups={}
    n=len(d["text"])
    for i in range(n):
     t=norm(d["text"][i])
     try: conf=float(d["conf"][i])
     except: conf=-1
     if len(t)<1 or conf<25:continue
     key=(d["block_num"][i],d["par_num"][i],d["line_num"][i])
     groups.setdefault(key,[]).append(i)
    items=[];logs=[]
    wr=(monitor_rect_for_window(self.hwnd) if self.capturemode.currentIndex()==2 else rect(self.hwnd))
    if not wr:return
    wx,wy,ww,wh=wr
    for ids in groups.values():
     text=norm(" ".join(d["text"][i] for i in ids))
     if len(text)<2:continue
     l=min(d["left"][i] for i in ids);top=min(d["top"][i] for i in ids)
     rr=max(d["left"][i]+d["width"][i] for i in ids);bb=max(d["top"][i]+d["height"][i] for i in ids)
     bw=max(50,rr-l);bh=max(24,bb-top)
     self.collect_terms(text)
     ko=self.translate_cached(text)
     # Coordinates relative to selected game window for the transparent overlay.
     absx=x+l;absy=y+top
     vals=[]
     for ii in ids:
      try:
       cv=float(d["conf"][ii])
       if cv>=0:vals.append(cv)
      except:pass
     cf=sum(vals)/len(vals) if vals else 0
     ukey=self.ui_key(l,top,bw,bh,w,h)
     stable=self.ui_translation(ukey,text,cf)
     if stable:ko=stable
     self.remember_ui(ukey,text,ko,cf)
     self.remember(text,ko,cf);self.add_timeline(text,ko,cf,ukey)
     bg=self.estimate_bg(im,l,top,rr,bb)
     # Slight padding hides anti-aliased source glyph edges.
     px=max(0,absx-wx-3);py=max(0,absy-wy-2)
     items.append((px,py,bw+6,bh+4,ko,bg));logs.append(text+" → "+ko)
    self.ov.hide()
    if items:self.fullov.set_items(items,wr);self.last_overlay_time=time.time();self.status.setPlainText("전체 화면 교체 후보:\n"+"\n".join(logs[:30]))
  except Exception as e:
   self.status.appendPlainText("캡처/OCR 오류: "+str(e));self.log_error("capture",e);self.recover_capture()
   if self.hwnd and "전체화면" in display_mode(self.hwnd):
    self.status.appendPlainText("독점 전체화면에서는 캡처/오버레이가 제한될 수 있습니다. 게임을 '무테두리 전체화면'으로 바꾸고 다시 시도하세요.")
  finally:
   try:self.adapt_interval(time.perf_counter()-started)
   except Exception:pass
   self.busy=False

 def closeEvent(self,e):
  try:self.timer.stop()
  except Exception:pass
  try:self.ov.close();self.fullov.close()
  except Exception:pass
  self.running=False;self.busy=False;self.backup_user_data();self.mark_session(False);e.accept()

app=QtWidgets.QApplication(sys.argv);m=Main();m.show();sys.exit(app.exec())
