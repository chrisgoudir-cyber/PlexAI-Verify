import time
from datetime import datetime
class MaintenanceService:
    STEPS=[('Scan de la bibliothèque',12),('Analyse FFprobe',14),('Extraction des images',10),('Calcul Video DNA',14),('Vérification IA locale',16),('Contrôle des collections',10),('Analyse qualité',10),('Recherche de doublons',8),('Génération du rapport',6)]
    def __init__(self,database): self.database=database
    def run_demo(self,progress):
        with self.database.connect() as c:
            run_id=c.execute("INSERT INTO maintenance_runs(status) VALUES('running')").lastrowid
        total=0
        for label,weight in self.STEPS:
            time.sleep(.12); total+=weight; progress(min(total,100),label)
        summary={'movies':self.database.scalar('SELECT COUNT(*) FROM movies') or 0,'issues':self.database.scalar('SELECT COUNT(*) FROM issues WHERE resolved=0') or 0}
        with self.database.connect() as c:
            c.execute("UPDATE maintenance_runs SET finished_at=?,status='completed',summary=? WHERE id=?",(datetime.now().isoformat(timespec='seconds'),str(summary),run_id))
        return summary
