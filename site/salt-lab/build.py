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
    site/salt-lab/index.html                   generated, tracked on main
    gh-pages branch                            index.html + .nojekyll, nothing else

--push builds a one-file commit straight onto `refs/heads/gh-pages` with git
plumbing -- no checkout, no second clone, and the working tree is never touched.
It pushes that one ref by name, so it cannot land on `main`. It is a no-op when
the regenerated page already matches what is published.

GitHub Pages serves that branch at https://me.zemingzhang.com/spark-experiments/
(the custom domain is configured on zemingzhang1.github.io, so this project page
inherits it).

Pushing needs the zemingzhang1 account active in gh. That is held per-shell: run
this from the PowerShell terminal where `gh auth status` lists that account as
active, not from a Git Bash shell, which may only see the other account.
"""

import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(REPO, "spark", "1_data_skew", "salting_simulator.html")
OUT = os.path.join(HERE, "index.html")
BRANCH = "gh-pages"
LIVE_URL = "https://me.zemingzhang.com/spark-experiments/"

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
    """Run a git command in the repository and return its stdout, or exit."""
    r = subprocess.run(("git",) + args, cwd=REPO, input=kw.get("input"),
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("git %s failed:\n%s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r.stdout.strip()


def published_sha():
    """Blob sha of index.html as currently published, or '' if there is none."""
    r = subprocess.run(["git", "ls-tree", "origin/" + BRANCH, "index.html"],
                       cwd=REPO, capture_output=True, text=True)
    parts = r.stdout.split()
    return parts[2] if r.returncode == 0 and len(parts) >= 3 else ""


def push():
    """Commit the generated page onto gh-pages and push, if it changed.

    Built with plumbing rather than a checkout: nothing in the working tree
    moves, and the push names one ref, so it can never reach main.
    """
    subprocess.run(["git", "fetch", "-q", "origin", BRANCH], cwd=REPO)
    blob = git("hash-object", "-w", OUT)
    if published_sha() == blob:
        print("push: the published page already matches, nothing to do")
        return

    nojekyll = git("hash-object", "-w", "--stdin", input="")
    tree = git("mktree", input="100644 blob %s\t.nojekyll\n100644 blob %s\tindex.html\n"
                               % (nojekyll, blob))
    parent = subprocess.run(["git", "rev-parse", "--verify", "-q", "origin/" + BRANCH],
                            cwd=REPO, capture_output=True, text=True).stdout.strip()
    args = ["commit-tree", tree]
    if parent:
        args += ["-p", parent]
    commit = git(*args, input="Publish Salt Lab from site/salt-lab/index.html\n")
    git("push", "-q", "origin", "%s:refs/heads/%s" % (commit, BRANCH))
    print("push: published %s to %s" % (commit[:9], BRANCH))
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
