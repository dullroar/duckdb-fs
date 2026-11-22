# Scripts index

<!-- IMMUTABLE HEADER: do not edit the text above the BEGIN marker. -->

This folder holds deterministic scripts for agents and CI: run, test, debug and build. CI scripts start here.

- Each script starts with a comment block that has a line `Run me when: <situation>` in its first 25 lines.
- Scripts must give the same result for the same input. Print clear errors and use exit code 0 only for success.
- Never put secrets or personal paths in a script. Read them from the environment.
- This file is generated. Run `python3 scripts/build_indexes.py` after any change. Do not edit the list below by hand.

Read the list. Run only the scripts whose "Run me when" line matches your task.

<!-- BEGIN GENERATED INDEX -->

* [build_context_indexes.py](./build_context_indexes.py)
  Run me when: an existing workflow uses the former command name for build_indexes.py.
* [build_indexes.py](./build_indexes.py)
  Run me when: I added, renamed, deleted or changed the gist of a memory, a plan or a script, and before every pull request.
* [check_context.py](./check_context.py)
  Run me when: I changed a context file or need to verify a pull request.
* [check_links.py](./check_links.py)
  Run me when: I changed or moved a Markdown file.
* [check_plan.py](./check_plan.py)
  Run me when: I created or changed a plan or step, or need to start a plan loop.
* [ctx_common.py](./ctx_common.py)
  Run me when: never directly. Other scripts in this folder import these helpers.
* [scan_context_secrets.py](./scan_context_secrets.py)
  Run me when: an existing workflow uses the former command name for scan_secrets.py.
* [scan_secrets.py](./scan_secrets.py)
  Run me when: I changed an agent contract or a document under docs, memory, references or plans.
* [test_docker.sh](./test_docker.sh)
  Run me when: I need to verify the project and its FUSE mount in Docker.

<!-- END GENERATED INDEX -->
