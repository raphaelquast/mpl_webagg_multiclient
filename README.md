# MPL - multi client webagg

Basic example for a multi-client setup with matplotlibs `webagg` backend.

- This will start a tornado server that spawns a new figure
  (and an associated websocket)on each `GET` request.

### Usage

1. Adjust the figure you want to show in `create_figure.py`
2. Start the server by running `server_multiclient.py` in a dedicated python terminal.
3. Open the created website (`localhost:8080` by default)
   - A new (independent) figure will be spawned each time a new page is created.