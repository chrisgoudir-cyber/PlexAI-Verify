from PySide6.QtCore import QObject, Signal, QThread
from app.audit import duplicate_groups, quality_assessment
from app.database import (
    clear_audit, save_movies, set_error, update_ai, update_audit,
    update_frames, update_metadata, update_tmdb,
    update_local_comparison, get_movies, get_movie,
    create_autopilot_run, add_autopilot_event,
    finish_autopilot_run,
)
from app.ffprobe import analyze_video
from app.image_extractor import build_video_dna,build_visual_hash,extract_frames
from app.ollama_ai import identify_movie, identify_movie_autopilot
from app.scanner import scan_movies
from app.express import express_decision
from app.local_compare import compare_with_local_ai
from app.media_support import classify_processing_error
from core.services.correction_service import CorrectionService

class BaseWorker(QObject):
    progress=Signal(int,int); log=Signal(str); finished=Signal(); error=Signal(str)
    def cancelled(self): return QThread.currentThread().isInterruptionRequested()

class ScanWorker(BaseWorker):
    def __init__(self,folder): super().__init__(); self.folder=folder
    def run(self):
        try:
            movies=scan_movies(self.folder); total=len(movies); self.log.emit(f'{total} films trouvés.')
            save_movies(movies); self.progress.emit(total,total); self.log.emit('Base SQLite mise à jour. Les fichiers modifiés seront réanalysés.')
        except Exception as exc: self.error.emit(str(exc))
        finally: self.finished.emit()

class MetadataWorker(BaseWorker):
    def __init__(self,movies,ffprobe_path,skip_done=False): super().__init__(); self.movies=movies; self.ffprobe_path=ffprobe_path; self.skip_done=skip_done
    def run(self):
        total=len(self.movies)
        try:
            for i,m in enumerate(self.movies,1):
                if self.cancelled(): self.log.emit('Traitement interrompu. La reprise sera possible.'); break
                if self.skip_done and m.get('analyzed') and m.get('analysis_state')!='changed': self.progress.emit(i,total); continue
                try: update_metadata(m['id'],analyze_video(m['filepath'],self.ffprobe_path))
                except Exception as exc:
                    code, message, action = classify_processing_error(m['filepath'], exc)
                    set_error(m['id'], message, code, action)
                    self.log.emit(f"{m['filename']} : {message} — {action}")
                self.progress.emit(i,total)
        except Exception as exc: self.error.emit(str(exc))
        finally: self.finished.emit()

class FramesWorker(BaseWorker):
    def __init__(self,movies,ffmpeg_path,frame_count,skip_done=False): super().__init__(); self.movies=movies; self.ffmpeg_path=ffmpeg_path; self.frame_count=frame_count; self.skip_done=skip_done
    def run(self):
        total=len(self.movies)
        try:
            for i,m in enumerate(self.movies,1):
                if self.cancelled(): self.log.emit('Traitement interrompu.'); break
                if self.skip_done and m.get('frames_ready') and m.get('analysis_state')!='changed': self.progress.emit(i,total); continue
                try:
                    frames=extract_frames(m['filepath'],float(m.get('duration') or 0),self.ffmpeg_path,self.frame_count)
                    update_frames(m['id'],build_visual_hash(frames),build_video_dna(frames))
                except Exception as exc:
                    code, message, action = classify_processing_error(m['filepath'], exc)
                    set_error(m['id'], message, code, action)
                    self.log.emit(f"{m['filename']} : {message} — {action}")
                self.progress.emit(i,total)
        except Exception as exc: self.error.emit(str(exc))
        finally: self.finished.emit()

class AIWorker(BaseWorker):
    def __init__(self,movies,ffmpeg_path,frame_count,url,model,skip_done=False): super().__init__(); self.movies=movies; self.ffmpeg_path=ffmpeg_path; self.frame_count=frame_count; self.url=url; self.model=model; self.skip_done=skip_done
    def run(self):
        total=len(self.movies)
        try:
            for i,m in enumerate(self.movies,1):
                if self.cancelled(): self.log.emit('Analyse IA interrompue.'); break
                if self.skip_done and m.get('ai_status') and m.get('analysis_state')!='changed': self.progress.emit(i,total); continue
                try:
                    frames=extract_frames(
                        m['filepath'],
                        float(m.get('duration') or 0),
                        self.ffmpeg_path,
                        self.frame_count,
                    )
                    ai_result = identify_movie(
                        frames,
                        m['filename'],
                        self.url,
                        self.model,
                    )
                    update_ai(m['id'], ai_result)

                    fresh = dict(m)
                    fresh.update({
                        "ai_title": ai_result.get("title"),
                        "ai_year": ai_result.get("year"),
                        "ai_confidence": ai_result.get("confidence"),
                        "ai_status": ai_result.get("status"),
                    })
                    comparison = compare_with_local_ai(
                        fresh,
                        "{title} ({year})",
                    )
                    update_local_comparison(m['id'], comparison)
                    self.log.emit(
                        f"{m['filename']} : "
                        f"{comparison.get('comparison_message')} — "
                        f"{comparison.get('proposed_filename')}"
                    )
                except Exception as exc:
                    code, message, action = classify_processing_error(m['filepath'], exc)
                    set_error(m['id'], message, code, action)
                    self.log.emit(f"{m['filename']} : {message} — {action}")
                self.progress.emit(i,total)
        except Exception as exc: self.error.emit(str(exc))
        finally: self.finished.emit()

class AuditWorker(BaseWorker):
    def __init__(self,movies): super().__init__(); self.movies=movies
    def run(self):
        total=len(self.movies)
        try:
            clear_audit(); groups,sims=duplicate_groups(self.movies)
            for i,m in enumerate(self.movies,1):
                if self.cancelled(): break
                flags,score=quality_assessment(m)
                update_audit(m['id'],groups.get(m['id']),sims.get(m['id']), ' | '.join(flags),score)
                self.progress.emit(i,total)
            self.log.emit(f"Audit terminé : {len(set(groups.values()))} groupe(s) DNA.")
        except Exception as exc: self.error.emit(str(exc))
        finally: self.finished.emit()


class ProfileWorker(BaseWorker):
    def __init__(
        self, movies, profile, ffprobe, ffmpeg,
        frames, url, model, skip_unchanged=True
    ):
        super().__init__()
        self.movies = movies
        self.profile = profile
        self.ffprobe = ffprobe
        self.ffmpeg = ffmpeg
        self.frames = frames
        self.url = url
        self.model = model
        self.skip = skip_unchanged

    def _record_error(self, movie, exc):
        code, message, action = classify_processing_error(
            movie["filepath"],
            exc,
        )
        set_error(movie["id"], message, code, action)
        self.log.emit(
            f"{movie['filename']} : {message} — {action}"
        )

    def run(self):
        stages = (
            1 if self.profile == "Rapide"
            else 2 if self.profile == "Complet"
            else 3
        )
        total = max(1, len(self.movies) * stages)
        done = 0

        try:
            for movie in self.movies:
                if self.cancelled():
                    break

                should_skip = (
                    self.skip
                    and movie.get("analyzed")
                    and movie.get("analysis_state") != "changed"
                )
                if not should_skip:
                    try:
                        update_metadata(
                            movie["id"],
                            analyze_video(
                                movie["filepath"],
                                self.ffprobe,
                            ),
                        )
                    except Exception as exc:
                        self._record_error(movie, exc)

                done += 1
                self.progress.emit(done, total)

            if (
                self.profile in ("Complet", "Expert")
                and not self.cancelled()
            ):
                from app.database import get_movie

                for movie in self.movies:
                    if self.cancelled():
                        break

                    should_skip = (
                        self.skip
                        and movie.get("frames_ready")
                        and movie.get("analysis_state") != "changed"
                    )
                    if not should_skip:
                        try:
                            fresh_row = get_movie(movie["id"])
                            fresh = (
                                dict(fresh_row)
                                if fresh_row
                                else movie
                            )
                            frames = extract_frames(
                                fresh["filepath"],
                                float(fresh.get("duration") or 0),
                                self.ffmpeg,
                                self.frames,
                            )
                            update_frames(
                                movie["id"],
                                build_visual_hash(frames),
                                build_video_dna(frames),
                            )
                        except Exception as exc:
                            self._record_error(movie, exc)

                    done += 1
                    self.progress.emit(done, total)

            if (
                self.profile == "Expert"
                and not self.cancelled()
            ):
                from app.database import get_movie

                for movie in self.movies:
                    if self.cancelled():
                        break

                    should_skip = (
                        self.skip
                        and movie.get("ai_status")
                        and movie.get("analysis_state") != "changed"
                    )
                    if not should_skip:
                        try:
                            fresh_row = get_movie(movie["id"])
                            fresh = (
                                dict(fresh_row)
                                if fresh_row
                                else movie
                            )
                            frames = extract_frames(
                                fresh["filepath"],
                                float(fresh.get("duration") or 0),
                                self.ffmpeg,
                                self.frames,
                            )
                            update_ai(
                                movie["id"],
                                identify_movie(
                                    frames,
                                    movie["filename"],
                                    self.url,
                                    self.model,
                                ),
                            )
                        except Exception as exc:
                            self._record_error(movie, exc)

                    done += 1
                    self.progress.emit(done, total)

            self.log.emit(
                f"Profil {self.profile} terminé. "
                "Lance ensuite l’audit DNA/qualité."
            )
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


from app.tmdb_client import compare_movie
from app.renamer import rename_movie



class LocalCompareWorker(BaseWorker):
    def __init__(self, movies, rename_template):
        super().__init__()
        self.movies = movies
        self.rename_template = rename_template

    def run(self):
        total = len(self.movies)
        try:
            for index, movie in enumerate(self.movies, 1):
                if self.cancelled():
                    self.log.emit("Comparaison IA locale interrompue.")
                    break
                try:
                    result = compare_with_local_ai(movie, self.rename_template)
                    update_local_comparison(movie["id"], result)
                    score = float(result.get("comparison_score") or 0) * 100
                    self.log.emit(
                        f"{movie['filename']} → {result['proposed_filename']} "
                        f"({score:.1f} %, {result['comparison_status']})"
                    )
                except Exception as exc:
                    code, message, action = classify_processing_error(
                        movie["filepath"], exc
                    )
                    set_error(movie["id"], message, code, action)
                    self.log.emit(
                        f"{movie['filename']} : {message} — {action}"
                    )
                self.progress.emit(index, total)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

class TMDbWorker(BaseWorker):
    def __init__(self, movies, token, language, rename_template):
        super().__init__()
        self.movies = movies
        self.token = token
        self.language = language
        self.rename_template = rename_template

    def run(self):
        total = len(self.movies)
        try:
            for index, movie in enumerate(self.movies, 1):
                if self.cancelled():
                    self.log.emit("Comparaison TMDb interrompue.")
                    break
                try:
                    result = compare_movie(
                        movie,
                        self.token,
                        self.language,
                        self.rename_template,
                    )
                    update_tmdb(movie["id"], result)
                    score = float(result.get("score") or 0) * 100
                    title = result.get("title") or "Aucun résultat"
                    self.log.emit(
                        f"{movie['filename']} → {title} ({score:.1f} %)"
                    )
                except Exception as exc:
                    code, message, action = classify_processing_error(
                        movie["filepath"], exc
                    )
                    set_error(movie["id"], message, code, action)
                    self.log.emit(
                        f"{movie['filename']} : {message} — {action}"
                    )
                self.progress.emit(index, total)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class RenameWorker(BaseWorker):
    def __init__(self, movies, dry_run, minimum_score):
        super().__init__()
        self.movies = movies
        self.dry_run = dry_run
        self.minimum_score = minimum_score

    def run(self):
        total = len(self.movies)
        renamed = 0
        skipped = 0
        try:
            for index, movie in enumerate(self.movies, 1):
                if self.cancelled():
                    self.log.emit("Renommage interrompu.")
                    break
                try:
                    result = rename_movie(
                        movie,
                        dry_run=self.dry_run,
                        minimum_score=self.minimum_score,
                    )
                    self.log.emit(result["message"])
                    if result["changed"]:
                        renamed += 1
                    else:
                        skipped += 1
                except Exception as exc:
                    skipped += 1
                    self.log.emit(f"IGNORÉ : {movie['filename']} — {exc}")
                self.progress.emit(index, total)

            mode = "simulation" if self.dry_run else "renommage"
            self.log.emit(
                f"Fin {mode} : {renamed} modification(s), "
                f"{skipped} fichier(s) ignoré(s)."
            )
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class HybridWorker(BaseWorker):
    """
    Analyse adaptative :
    - conserve les films dont le nom est déjà propre ;
    - réserve Ollama aux noms ambigus, génériques ou très bruités ;
    - ne renomme jamais directement.
    """
    def __init__(
        self, movies, ffmpeg_path, frame_count,
        url, model, skip_done=True
    ):
        super().__init__()
        self.movies = movies
        self.ffmpeg_path = ffmpeg_path
        self.frame_count = max(3, min(int(frame_count), 6))
        self.url = url
        self.model = model
        self.skip_done = skip_done

    def run(self):
        total = len(self.movies)
        ai_count = 0
        express_count = 0
        try:
            for index, movie in enumerate(self.movies, 1):
                if self.cancelled():
                    self.log.emit("Analyse hybride interrompue.")
                    break

                decision = express_decision(movie)
                if not decision["needs_ai"]:
                    express_count += 1
                    self.log.emit(
                        f"EXPRESS : {movie['filename']} — "
                        f"{decision['reason']}"
                    )
                    self.progress.emit(index, total)
                    continue

                if (
                    self.skip_done
                    and movie.get("ai_status")
                    and movie.get("analysis_state") != "changed"
                ):
                    self.progress.emit(index, total)
                    continue

                try:
                    frames = extract_frames(
                        movie["filepath"],
                        float(movie.get("duration") or 0),
                        self.ffmpeg_path,
                        self.frame_count,
                    )
                    result = identify_movie(
                        frames,
                        movie["filename"],
                        self.url,
                        self.model,
                    )
                    update_ai(movie["id"], result)

                    fresh = dict(movie)
                    fresh.update({
                        "ai_title": result.get("title"),
                        "ai_year": result.get("year"),
                        "ai_confidence": result.get("confidence"),
                        "ai_status": result.get("status"),
                    })
                    comparison = compare_with_local_ai(
                        fresh,
                        "{title} ({year})",
                    )
                    update_local_comparison(movie["id"], comparison)

                    ai_count += 1
                    self.log.emit(
                        f"IA : {movie['filename']} → "
                        f"{result.get('title') or 'incertain'} "
                        f"({float(result.get('confidence') or 0) * 100:.1f} %) — "
                        f"{comparison.get('comparison_message')}"
                    )
                except Exception as exc:
                    code, message, action = classify_processing_error(
                        movie["filepath"], exc
                    )
                    set_error(movie["id"], message, code, action)
                    self.log.emit(
                        f"{movie['filename']} : {message} — {action}"
                    )

                self.progress.emit(index, total)

            self.log.emit(
                f"Analyse hybride terminée : {express_count} en mode Express, "
                f"{ai_count} soumis à l’IA."
            )
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()



class AllInOneWorker(BaseWorker):
    """
    Pipeline automatique et sécurisé :

    1. scanne la bibliothèque ;
    2. analyse les métadonnées ;
    3. extrait plusieurs images ;
    4. demande à l'IA si le contenu est bien un film ;
    5. vérifie le titre et l'année ;
    6. renomme uniquement si le nom est incorrect et si la confiance
       IA est au moins égale à 95 % ;
    7. conserve un historique annulable.

    Le worker ne supprime jamais de fichier et ne déplace jamais un film.
    """

    MINIMUM_CONFIDENCE = 0.95

    def __init__(
        self,
        folder,
        ffprobe_path,
        ffmpeg_path,
        frame_count,
        url,
        model,
        rename_template="{title} ({year})",
        skip_unchanged=True,
    ):
        super().__init__()
        self.folder = folder
        self.ffprobe_path = ffprobe_path
        self.ffmpeg_path = ffmpeg_path
        self.frame_count = max(4, min(int(frame_count), 6))
        self.url = url
        self.model = model
        self.rename_template = rename_template or "{title} ({year})"
        self.skip_unchanged = skip_unchanged
        self.corrections = CorrectionService()

    def _event(
        self, run_id, movie, action, confidence=0, message=""
    ):
        add_autopilot_event(
            run_id,
            movie.get("id"),
            movie.get("filename"),
            action,
            confidence,
            message,
        )

    def run(self):
        summary = {
            "verified": 0,
            "already_correct": 0,
            "renamed": 0,
            "uncertain": 0,
            "non_movie": 0,
            "errors": 0,
        }
        run_id = None

        try:
            self.log.emit("TOUT-EN-UN — Étape 1/5 : scan de la bibliothèque…")
            scanned = scan_movies(self.folder)
            save_movies(scanned)
            movies = [dict(row) for row in get_movies("", "Tous")]
            run_id = create_autopilot_run(len(movies))

            if not movies:
                self.log.emit("Aucun film trouvé.")
                finish_autopilot_run(run_id, summary, "done")
                return

            total_steps = max(1, len(movies) * 4)
            done = 0

            for position, initial_movie in enumerate(movies, 1):
                if self.cancelled():
                    self.log.emit(
                        "TOUT-EN-UN interrompu. Les résultats déjà validés sont conservés."
                    )
                    finish_autopilot_run(run_id, summary, "cancelled")
                    return

                movie = dict(initial_movie)
                label = f"[{position}/{len(movies)}] {movie['filename']}"
                self.log.emit(f"{label} — vérification")

                try:
                    # Étape 2 : métadonnées
                    must_analyze = (
                        not self.skip_unchanged
                        or not movie.get("analyzed")
                        or movie.get("analysis_state") == "changed"
                    )
                    if must_analyze:
                        metadata = analyze_video(
                            movie["filepath"], self.ffprobe_path
                        )
                        update_metadata(movie["id"], metadata)

                    done += 1
                    self.progress.emit(done, total_steps)

                    fresh_row = get_movie(movie["id"])
                    movie = dict(fresh_row) if fresh_row else movie
                    duration = float(movie.get("duration") or 0)
                    if duration <= 0:
                        raise RuntimeError(
                            "Durée vidéo indisponible : extraction impossible."
                        )

                    # Étape 3 : images + Video DNA
                    frames = extract_frames(
                        movie["filepath"],
                        duration,
                        self.ffmpeg_path,
                        self.frame_count,
                    )
                    update_frames(
                        movie["id"],
                        build_visual_hash(frames),
                        build_video_dna(frames),
                    )

                    done += 1
                    self.progress.emit(done, total_steps)

                    # Étape 4 : vérification stricte par IA
                    result = identify_movie_autopilot(
                        frames,
                        movie["filename"],
                        self.url,
                        self.model,
                    )
                    update_ai(movie["id"], result)
                    confidence = float(result.get("confidence") or 0)
                    summary["verified"] += 1

                    done += 1
                    self.progress.emit(done, total_steps)

                    if (
                        not result.get("is_movie", True)
                        or result.get("status") == "not_movie"
                    ):
                        summary["non_movie"] += 1
                        message = (
                            "Le contenu n'est pas identifié comme un long métrage. "
                            "Aucune modification."
                        )
                        self._event(
                            run_id, movie, "non_movie", confidence, message
                        )
                        self.log.emit(
                            f"{label} — NON FILM / contrôle manuel "
                            f"({confidence * 100:.1f} %)"
                        )
                        done += 1
                        self.progress.emit(done, total_steps)
                        continue

                    fresh = dict(movie)
                    fresh.update({
                        "ai_title": result.get("title"),
                        "ai_year": result.get("year"),
                        "ai_confidence": confidence,
                        "ai_status": result.get("status"),
                    })
                    comparison = compare_with_local_ai(
                        fresh, self.rename_template
                    )
                    update_local_comparison(movie["id"], comparison)

                    status = comparison.get("comparison_status")
                    score = float(comparison.get("comparison_score") or 0)

                    # Nom déjà correct : rien à modifier.
                    if status == "confirmed" or result.get("status") == "correct":
                        summary["already_correct"] += 1
                        message = (
                            f"Nom déjà correct — confiance "
                            f"{confidence * 100:.1f} %."
                        )
                        self._event(
                            run_id, movie, "already_correct",
                            confidence, message
                        )
                        self.log.emit(f"{label} — OK, nom conservé")
                        done += 1
                        self.progress.emit(done, total_steps)
                        continue

                    # Renommage automatique uniquement à partir de 95 %.
                    can_rename = (
                        result.get("status") == "mismatch"
                        and status in {"rename", "mismatch"}
                        and confidence >= self.MINIMUM_CONFIDENCE
                        and score >= self.MINIMUM_CONFIDENCE
                    )

                    if not can_rename:
                        summary["uncertain"] += 1
                        message = (
                            f"Résultat non automatique : statut={status}, "
                            f"confiance={confidence * 100:.1f} %. "
                            "Contrôle manuel requis."
                        )
                        self._event(
                            run_id, movie, "manual_review",
                            confidence, message
                        )
                        self.log.emit(
                            f"{label} — CONTRÔLE MANUEL "
                            f"({confidence * 100:.1f} %)"
                        )
                        done += 1
                        self.progress.emit(done, total_steps)
                        continue

                    correction_results = self.corrections.apply([movie["id"]])
                    correction = (
                        correction_results[0]
                        if correction_results
                        else None
                    )

                    if correction and correction.status == "done":
                        summary["renamed"] += 1
                        self._event(
                            run_id, movie, "renamed",
                            confidence, correction.message
                        )
                        self.log.emit(
                            f"{label} — CORRIGÉ AUTOMATIQUEMENT : "
                            f"{correction.message}"
                        )
                    else:
                        summary["uncertain"] += 1
                        message = (
                            correction.message
                            if correction
                            else "Correction bloquée par les règles de sécurité."
                        )
                        self._event(
                            run_id, movie, "rename_blocked",
                            confidence, message
                        )
                        self.log.emit(
                            f"{label} — RENOMMAGE BLOQUÉ : {message}"
                        )

                    done += 1
                    self.progress.emit(done, total_steps)

                except Exception as exc:
                    summary["errors"] += 1
                    code, message, action = classify_processing_error(
                        movie["filepath"], exc
                    )
                    set_error(movie["id"], message, code, action)
                    self._event(
                        run_id, movie, "error", 0,
                        f"{message} — {action}"
                    )
                    self.log.emit(
                        f"{label} — ERREUR : {message} — {action}"
                    )
                    # Avance jusqu'à la fin des 4 étapes réservées à ce film.
                    target = position * 4
                    done = max(done, target)
                    self.progress.emit(min(done, total_steps), total_steps)

            finish_autopilot_run(run_id, summary, "done")
            self.log.emit(
                "TOUT-EN-UN TERMINÉ — "
                f"{summary['verified']} vérifié(s), "
                f"{summary['already_correct']} déjà correct(s), "
                f"{summary['renamed']} renommé(s), "
                f"{summary['uncertain']} à contrôler, "
                f"{summary['non_movie']} non-film(s), "
                f"{summary['errors']} erreur(s)."
            )

        except Exception as exc:
            if run_id is not None:
                finish_autopilot_run(run_id, summary, "error")
            self.error.emit(str(exc))
        finally:
            self.finished.emit()
