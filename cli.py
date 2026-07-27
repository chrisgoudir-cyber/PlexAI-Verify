import argparse
from app.application_api import app_api

def main():
    parser=argparse.ArgumentParser(prog='plexai-verify')
    parser.add_argument('command', choices=['health','issues'])
    args=parser.parse_args()
    if args.command=='health':
        d=app_api.library.dashboard(); s=d['stats']
        print(f"Films: {s.total}")
        print(f"Santé: {d['health_exact']:.2f} %")
        print(d['headline'])
    else:
        for issue in app_api.audit.issues():
            print(f"[{issue.issue_type}] {issue.filename} — {issue.cause}")

if __name__=='__main__': main()
