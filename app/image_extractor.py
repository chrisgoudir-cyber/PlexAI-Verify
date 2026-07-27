import hashlib, subprocess
from pathlib import Path
import imagehash
from PIL import Image
from app.paths import FRAMES_DIR

def movie_cache_dir(filepath: str) -> Path:
    key=hashlib.sha1(filepath.encode('utf-8',errors='ignore')).hexdigest()
    path=FRAMES_DIR/key; path.mkdir(parents=True,exist_ok=True); return path

def extract_frames(filepath: str,duration: float,ffmpeg_path: str,count: int=8)->list[Path]:
    if duration<=0: raise ValueError('Durée vidéo inconnue.')
    exe=Path(ffmpeg_path)
    if not exe.exists(): raise FileNotFoundError(f'FFmpeg introuvable : {ffmpeg_path}')
    outdir=movie_cache_dir(filepath); frames=[]
    positions=[duration*(0.06+(0.88*i/max(count-1,1))) for i in range(count)]
    for i,pos in enumerate(positions,1):
        output=outdir/f'frame_{i:02d}.jpg'
        cmd=[str(exe),'-hide_banner','-loglevel','error','-ss',f'{pos:.3f}','-i',filepath,'-frames:v','1','-vf','scale=640:-2','-q:v','4','-y',str(output)]
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        if result.returncode!=0 or not output.exists(): raise RuntimeError(result.stderr.strip() or "Extraction d'image impossible.")
        frames.append(output)
    return frames

def frame_hashes(frames:list[Path])->list[str]:
    values=[]
    for frame in frames:
        with Image.open(frame) as image:
            values.append(str(imagehash.phash(image.convert('RGB'))))
    return values

def build_visual_hash(frames:list[Path])->str:
    return '-'.join(frame_hashes(frames))

def build_video_dna(frames:list[Path])->str:
    hashes=frame_hashes(frames)
    return f"DNA1:{len(hashes)}:"+'|'.join(hashes)
