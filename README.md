# MPL - multi client webagg

Basic example for a multi-client setup with matplotlibs `webagg` backend.

- This will start a tornado server that spawns a new figure
  (and an associated websocket)on each `GET` request.