from PySide6.QtCore import QThread,Signal
from PySide6.QtWidgets import *
STYLE="""QMainWindow{background:#101216} QWidget{color:#f4f4f4;font-family:Segoe UI;font-size:13px} QFrame#Sidebar{background:#171a20;border-right:1px solid #292d36} QPushButton{background:#242832;border:1px solid #333845;border-radius:8px;padding:10px;text-align:left} QPushButton:hover{background:#303541} QPushButton#Primary{background:#e5a00d;color:#111;font-weight:700;text-align:center;padding:14px} QFrame#Card{background:#191d24;border:1px solid #2c313b;border-radius:12px} QLabel#Title{font-size:28px;font-weight:700} QLabel#Metric{font-size:26px;font-weight:700} QProgressBar{border:1px solid #333845;border-radius:7px;background:#1d2128;height:14px} QProgressBar::chunk{background:#e5a00d;border-radius:6px}"""
class Worker(QThread):
    progress=Signal(int,str); done=Signal(dict); failed=Signal(str)
    def __init__(self,s): super().__init__(); self.s=s
    def run(self):
        try:self.done.emit(self.s.run_demo(self.progress.emit))
        except Exception as e:self.failed.emit(str(e))
class Card(QFrame):
    def __init__(self,title,value,detail):
        super().__init__(); self.setObjectName('Card'); l=QVBoxLayout(self); l.addWidget(QLabel(title)); v=QLabel(value); v.setObjectName('Metric'); l.addWidget(v); l.addWidget(QLabel(detail))
class MainWindow(QMainWindow):
    def __init__(self,db,service):
        super().__init__(); self.db=db; self.service=service; self.setWindowTitle('PlexAI Verify X Pro'); self.resize(1400,850); self.setStyleSheet(STYLE)
        c=QWidget(); root=QHBoxLayout(c); root.setContentsMargins(0,0,0,0); side=QFrame(); side.setObjectName('Sidebar'); side.setFixedWidth(245); sl=QVBoxLayout(side); logo=QLabel('PLEXAI VERIFY'); logo.setStyleSheet('font-size:18px;font-weight:800;padding:8px'); sl.addWidget(logo)
        self.stack=QStackedWidget(); self.dashboard=QWidget(); dl=QVBoxLayout(self.dashboard); dl.setContentsMargins(28,24,28,24); t=QLabel('PlexAI Verify X Pro'); t.setObjectName('Title'); dl.addWidget(t); dl.addWidget(QLabel("Vue d'ensemble de votre bibliothèque")); p=QProgressBar(); p.setValue(94); p.setFormat('Santé de la bibliothèque : %p %'); dl.addWidget(p); self.grid=QGridLayout(); dl.addLayout(self.grid); self.btn=QPushButton('▶  MAINTENANCE AUTOMATIQUE'); self.btn.setObjectName('Primary'); self.btn.clicked.connect(self.start); dl.addWidget(self.btn); dl.addStretch(); self.stack.addWidget(self.dashboard)
        home=QPushButton('🏠  Tableau de bord'); home.clicked.connect(lambda:self.stack.setCurrentIndex(0)); sl.addWidget(home)
        mods=[('🎞','Bibliothèque'),('🧠','Analyse IA'),('🎬','Collections'),('➕','Acquisition'),('⭐','Qualité'),('🧬','Video DNA'),('💬','Assistant IA'),('📄','Rapports'),('⚙','Paramètres')]
        for icon,name in mods:
            page=QWidget(); pl=QVBoxLayout(page); h=QLabel(f'{icon}  {name}'); h.setObjectName('Title'); pl.addWidget(h); card=QFrame(); card.setObjectName('Card'); cl=QVBoxLayout(card); cl.addWidget(QLabel('Module prêt à recevoir les fonctions v10/v13.')); pl.addWidget(card); pl.addStretch(); idx=self.stack.addWidget(page); b=QPushButton(f'{icon}  {name}'); b.clicked.connect(lambda _,i=idx:self.stack.setCurrentIndex(i)); sl.addWidget(b)
        sl.addStretch(); sl.addWidget(QLabel('X Pro — Architecture 1.0')); root.addWidget(side); root.addWidget(self.stack,1); self.setCentralWidget(c); self.refresh()
    def refresh(self):
        while self.grid.count():
            w=self.grid.takeAt(0).widget(); w.deleteLater() if w else None
        movies=self.db.scalar('SELECT COUNT(*) FROM movies') or 0; issues=self.db.scalar('SELECT COUNT(*) FROM issues WHERE resolved=0') or 0
        vals=[('Films',str(movies),'Films indexés'),('Vérifiés IA','0','À raccorder'),('Collections','0','À détecter'),('Problèmes',str(issues),'À examiner'),('Qualité','0','À améliorer'),('Doublons','0','Video DNA'),('Audio FR','0','Manquants'),('Sous-titres FR','0','Manquants')]
        for i,x in enumerate(vals): self.grid.addWidget(Card(*x),i//4,i%4)
    def start(self):
        self.p=QProgressDialog('Préparation...','Annuler',0,100,self); self.p.setWindowTitle('Maintenance automatique'); self.p.setMinimumDuration(0); self.w=Worker(self.service); self.w.progress.connect(lambda v,l:(self.p.setValue(v),self.p.setLabelText(l))); self.w.done.connect(self.finished); self.w.failed.connect(lambda m:QMessageBox.critical(self,'Erreur',m)); self.w.start()
    def finished(self,r):
        self.p.close(); self.refresh(); QMessageBox.information(self,'Maintenance terminée',f"Films : {r['movies']}\nProblèmes : {r['issues']}")
