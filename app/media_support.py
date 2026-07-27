from __future__ import annotations

from pathlib import Path


class MediaSupportError(RuntimeError):
    def __init__(self, code, message, action):
        super().__init__(message)
        self.code = code
        self.action = action


def media_kind(filepath):
    extension = Path(filepath).suffix.lower()
    if extension == ".iso":
        return "ISO"
    if extension in {".m2ts", ".ts"}:
        return "Transport Stream"
    if extension == ".mkv":
        return "Matroska"
    if extension in {".mp4", ".m4v", ".mov"}:
        return "MP4 / QuickTime"
    if extension == ".avi":
        return "AVI"
    if extension == ".wmv":
        return "Windows Media"
    return extension.lstrip(".").upper() or "Inconnu"


def validate_media_source(filepath):
    path = Path(filepath)
    if not path.exists():
        raise MediaSupportError(
            "FILE_MISSING",
            "Le fichier n'est plus accessible.",
            "Vérifier le NAS ou relancer le scan de la bibliothèque.",
        )

    if path.suffix.lower() == ".iso":
        raise MediaSupportError(
            "ISO_REQUIRES_MOUNT",
            "Image disque ISO détectée. FFprobe ne peut pas analyser directement "
            "la structure Blu-ray/DVD contenue dans cette image.",
            "Dans l'Explorateur Windows, clic droit sur l'ISO > Monter. "
            "Analyse ensuite le plus grand fichier du dossier BDMV\\STREAM "
            "(extension .m2ts), ou convertis l'ISO en MKV sans réencodage.",
        )


def classify_processing_error(filepath, error):
    if isinstance(error, MediaSupportError):
        return error.code, str(error), error.action

    raw = str(error).strip()
    lower = raw.lower()
    extension = Path(filepath).suffix.lower()

    if extension == ".iso":
        return (
            "ISO_REQUIRES_MOUNT",
            "Image ISO non analysable directement.",
            "Monter l'ISO dans Windows puis analyser le plus grand fichier "
            "BDMV\\STREAM\\*.m2ts, ou convertir l'ISO en MKV.",
        )

    if "invalid as first byte of an ebml" in lower or "ebml" in lower:
        return (
            "INVALID_MATROSKA",
            "Le fichier porte une extension Matroska, mais sa structure MKV "
            "est invalide ou endommagée.",
            "Tester la lecture dans VLC. Si elle échoue, remplacer le fichier. "
            "Si elle fonctionne, remuxer avec MKVToolNix.",
        )

    if "invalid data found" in lower:
        return (
            "INVALID_MEDIA",
            "FFprobe ne reconnaît pas correctement la structure du fichier.",
            "Tester le fichier dans VLC puis le remuxer sans réencodage avec "
            "MKVToolNix ou FFmpeg.",
        )

    if "permission denied" in lower or "access is denied" in lower:
        return (
            "ACCESS_DENIED",
            "Accès refusé au fichier.",
            "Vérifier les autorisations du partage NAS et les identifiants Windows.",
        )

    if "no such file" in lower or "introuvable" in lower:
        return (
            "FILE_MISSING",
            "Le fichier est introuvable ou le NAS est déconnecté.",
            "Reconnecter le partage réseau puis relancer le scan.",
        )

    if "timed out" in lower or "timeout" in lower:
        return (
            "TIMEOUT",
            "L'analyse a dépassé le délai autorisé.",
            "Vérifier la connexion au NAS, puis réessayer uniquement sur ce film.",
        )

    return (
        "PROCESSING_ERROR",
        raw[:500] or "Erreur inconnue pendant l'analyse.",
        "Réessayer sur ce film. Si l'erreur persiste, tester sa lecture dans VLC.",
    )
