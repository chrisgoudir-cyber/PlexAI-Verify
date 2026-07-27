from html import escape
from pathlib import Path
from plexai_verify.app.audit_summary import build_audit_summary
from plexai_verify.app.scoring import global_confidence


def export_audit_html(movies, output_path):
    summary = build_audit_summary(movies)
    rows = []

    for movie in movies:
        result = global_confidence(movie)
        rows.append(
            "<tr>"
            f"<td>{escape(str(movie.get('filename') or ''))}</td>"
            f"<td>{escape(str(movie.get('ai_title') or '—'))}</td>"
            f"<td>{escape(str(movie.get('ai_year') or '—'))}</td>"
            f"<td>{result['score']} %</td>"
            f"<td>{escape(result['verdict'])}</td>"
            f"<td>{escape(str(movie.get('comparison_message') or '—'))}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Audit PlexAI Verify</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:30px;background:#111;color:#eee}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}}
.card{{background:#1f1f1f;border:1px solid #333;border-radius:10px;padding:18px}}
.value{{font-size:28px;font-weight:700}}
table{{width:100%;border-collapse:collapse;background:#1a1a1a}}
th,td{{padding:10px;border-bottom:1px solid #333;text-align:left}}
th{{background:#242424}}
</style>
</head>
<body>
<h1>Audit PlexAI Verify</h1>
<p>{summary['total']} films analysés</p>
<div class="cards">
<div class="card"><div class="value">{summary['conformes']}</div>Conformes</div>
<div class="card"><div class="value">{summary['a_verifier']}</div>À vérifier</div>
<div class="card"><div class="value">{summary['a_renommer']}</div>À renommer</div>
<div class="card"><div class="value">{summary['doublons']}</div>Doublons</div>
<div class="card"><div class="value">{summary['erreurs']}</div>Erreurs</div>
<div class="card"><div class="value">{summary['sans_audio_fr']}</div>Sans audio FR</div>
<div class="card"><div class="value">{summary['sans_sous_titres']}</div>Sans sous-titres</div>
<div class="card"><div class="value">{summary['qualite_moyenne']} %</div>Score moyen</div>
</div>
<table>
<thead>
<tr><th>Fichier</th><th>Titre IA</th><th>Année</th><th>Score global</th><th>Verdict</th><th>Comparaison</th></tr>
</thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body>
</html>"""

    path = Path(output_path)
    path.write_text(html, encoding="utf-8")
    return str(path)
