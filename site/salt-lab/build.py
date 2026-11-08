"""Wrap the Salt Lab artifact source in a real HTML document for static hosting.

The artifact platform supplies the doctype, charset, viewport and a small reset
at publish time, so the source file starts straight at <title>. Anywhere else --
GitHub Pages, S3, a plain web server -- those have to be supplied here, or the
page renders in quirks mode and every non-ASCII character (. -> - x) comes out
mangled.

The shell also stamps data-theme="dark" on <html>. Inside the artifact the page
follows the Claude app's theme; hosted standalone it would otherwise follow each
visitor's OS setting, and this page is meant to be seen dark.

    python site/salt-lab/build.py            # regenerate index.html
    python site/salt-lab/build.py --push     # regenerate, then publish if changed

Layout:

    spark/1_data_skew/salting_simulator.html   the source, edited in the artifact
    site/salt-lab/index.html                   generated, tracked here
    site/salt-lab/.deploy/                     clone of zemingzhang1/spark-salt-lab,
                                               git-ignored; --push copies index.html
                                               in and pushes it

--push only touches the deploy clone, never this repository, and it refuses to
run if that clone's origin is not the Pages repo. It is a no-op when the
regenerated page is byte-identical to what is already published, so it is safe
to run whenever you are unsure.

Pushing needs the zemingzhang1 account active in gh. That is held per-shell: run
this from the PowerShell terminal where `gh auth status` lists that account as
active, not from a Git Bash shell, which may only see the other account.
"""

import io
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(REPO, "spark", "1_data_skew", "salting_simulator.html")
OUT = os.path.join(HERE, "index.html")
DEPLOY = os.path.join(HERE, ".deploy")
DEPLOY_REMOTE = "https://github.com/zemingzhang1/spark-salt-lab.git"
LIVE_URL = "https://me.zemingzhang.com/spark-salt-lab/"

# What the artifact skeleton provides and a static host does not.
SHELL_HEAD = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="An interactive Spark data-skew and salting simulator: dial in a skewed dataset, then watch the salt spread it across shuffle partitions.">
<style>
  :root {
    color-scheme: dark;
    padding-top: env(safe-area-inset-top, 0px);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
  body { margin: 0; font-size: 14px; font-family: system-ui, -apple-system, sans-serif; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
"""

SPLIT = '<div id="root"></div>'


def git(*args, **kw):
    """Run a git command in the deploy clone and return its stdout, or exit."""
    cwd = kw.pop("cwd", DEPLOY)
    r = subprocess.run(("git",) + args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("git %s failed:\n%s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r.stdout.strip()


def ensure_deploy():
    """Make sure .deploy is a clone of the Pages repo - and nothing else.

    The deploy clone is the only thing --push is allowed to commit to. Checking
    its remote here is what stops a stray push landing in spark-experiments.
    """
    if not os.path.isdir(os.path.join(DEPLOY, ".git")):
        print("cloning the Pages repo into %s ..." % os.path.normpath(DEPLOY))
        r = subprocess.run(["git", "clone", "-q", DEPLOY_REMOTE, DEPLOY])
        if r.returncode != 0:
            sys.exit("could not clone " + DEPLOY_REMOTE)
    url = git("remote", "get-url", "origin")
    if url.rstrip("/").removesuffix(".git") != DEPLOY_REMOTE.rstrip("/").removesuffix(".git"):
        sys.exit("refusing to publish: %s points at %s, not %s"
                 % (os.path.normpath(DEPLOY), url, DEPLOY_REMOTE))


def push():
    """Copy the generated page into the deploy clone and push, if it changed."""
    ensure_deploy()
    git("fetch", "-q", "origin")
    git("checkout", "-q", "main")
    git("reset", "-q", "--hard", "origin/main")
    shutil.copyfile(OUT, os.path.join(DEPLOY, "index.html"))
    if not git("status", "--porcelain", "--", "index.html"):
        print("push: the published page already matches, nothing to do")
        return
    git("add", "index.html")
    git("commit", "-q", "-m", "Rebuild page from the current artifact")
    git("push", "-q", "origin", "HEAD:main")
    print("push: published %s to %s" % (git("rev-parse", "--short", "HEAD"), DEPLOY_REMOTE))
    print("      Pages takes a few minutes, then %s updates" % LIVE_URL)


def main():
    if not os.path.exists(SRC):
        sys.exit("artifact source not found: " + os.path.normpath(SRC))

    src = io.open(SRC, encoding="utf-8").read()
    if SPLIT not in src:
        sys.exit('could not find \'%s\' -- has the artifact structure changed?' % SPLIT)

    head, body = src.split(SPLIT, 1)
    page = SHELL_HEAD + head.rstrip() + "\n</head>\n<body>\n" + SPLIT + body.rstrip() + "\n</body>\n</html>\n"

    before = io.open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(page)

    non_ascii = sum(1 for ch in page if ord(ch) > 127)
    print("wrote %s%s" % (os.path.normpath(OUT), "" if before != page else "  (no change)"))
    print("  %d bytes, %d non-ASCII characters (all safe under the charset above)"
          % (len(page.encode("utf-8")), non_ascii))
    for needed in ("<!doctype html>", '<meta charset="utf-8">', SPLIT, "</body>"):
        print("  contains %-24s %s" % (needed, "yes" if needed in page else "NO"))

    if "--push" in sys.argv[1:]:
        push()


if __name__ == "__main__":
    main()
