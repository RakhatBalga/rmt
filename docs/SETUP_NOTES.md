# Recorded setup history: 22 October 2026

[Back to README](../README.md)

This is the software-development record of the instrument setup on the team's
Windows 11 PC, followed by the protocol 2.0 work on a macOS laptop.

## Initial environment and recovery

- Python and Docker CLI were already installed.
- Docker Desktop initially failed to start with a dockerInference socket error
  (Windows error 1920: the file cannot be accessed by the system).
- After preserving Docker/run under a backup name, startup reached a second
  similar failure at docker-secrets-engine/engine.sock.
- Both runtime directories were preserved under backup names and Docker restarted.
  A failed intermediate restart recreated an unusable socket in the first
  directory, so it had to be prepared again before the successful common restart.
- No user images, volumes or containers were deleted during that recovery.
- The responding engine subsequently reported Docker Desktop 4.96.2, Engine 29.9.2,
  Linux/amd64. Earlier CLI output had shown 29.2.1 and the Desktop log 4.65.0.
  These are observed versions; the lab scripts did not perform a Docker update.
- The Python base image was downloaded successfully and pinned by digest in Dockerfile.

The backup directories recorded during recovery were:

```text
%LOCALAPPDATA%\Docker\run.backup-rmt-20261022
%LOCALAPPDATA%\Docker\run.backup-rmt-20261022-second
%LOCALAPPDATA%\docker-secrets-engine.backup-rmt-20261022
```

The reported workaround was found in
[Docker issue 554](https://github.com/docker/desktop-feedback/issues/554).
These historical notes do not assert that the paths still exist after later
manual changes or that every similar startup failure has the same cause.

## Software verification and measurements

Five software tests passed, covering actual local HTTP calls, 200/500/503
responses, timeout behavior, single-source decisions and confusion-matrix metrics.

The first attempt in the restricted environment could not connect to localhost.
The tests were rerun with local network access and passed. Those failed test
connections are not research observations. A subsequent check after explicitly
closing HTTPError responses passed without those resource warnings.

The original automated pilot is 20261022T100815Z-3082e0. Its verification summary
is validation.json at the project root. It covers 20 valid trials, 100 measured
requests, 140 unique trial/condition pairs, successful cleanup and an independent
accuracy calculation. It is not an automatic validator for all future runs.

A later completed pilot, 20261022T101634Z-23a61b, records operator Marlen and also
contains 20 valid trials with zero invalid trials. Its aggregate metrics agree
with the first pilot. The detailed results walkthrough uses this later collection.

## Documentation update

The project Markdown documentation was translated into English and expanded with
run instructions, file locations, data definitions and worked metric examples.
Original measurement files and code snapshots remain evidence from their respective
runs. Generated RESULTS.md files were already in English.

## If Docker startup fails again

Save the precise message and check `docker version` first. Read the current Docker
guidance or relevant issue before changing system runtime directories. The launcher
does not perform those recovery steps. Factory reset, volume deletion and WSL
unregistration are not required steps for running this experiment.

A failed collection is recorded as an error, not replaced by invented measurements.
