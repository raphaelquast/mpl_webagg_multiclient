# MPL - multi client webagg

Basic example for a multi-client setup using matplotlib with the `webagg` backend.

- This will start a tornado server that spawns a new figure
  (and an associated websocket) on each `GET` request.

### Usage

1. Adjust the figure you want to show in `create_figure.py`
2. Start the server by running `server_multiclient.py` in a dedicated python terminal.
3. Open the created website (`localhost:8080` by default)
   - A new (independent) figure will be spawned each time a new page is created.

![mpl_tornado_multiclient](https://github.com/raphaelquast/mpl_webagg_multiclient/assets/22773387/065ce1a9-a009-4fb3-8b0f-7566bcc224b4)
