# Airtable Addon
This is a the git repository for the **[airtable](https://www.airtable.com/)** addons.

This addon provides two elements for the AYON pipeline:
 * client - The AYON desktop integration.
 * services - Standalone dockerized daemons that act based on events (aka `leecher`, `processor` and `transmitter`).

### Settings
Settings for services and client.
Here you can set your airtable api key through `ayon+settings://airtable/service_settings/script_key`
which is your access token in Airtable. You can also set your base and table name for service sync and publish
eidtorial return through client addon.
Users can create access token for Airtable through `https://airtable.com/create/tokens` with
all scopes and your workspace.The key needs to be stored at `{YOUR_AYON_SERVER_URL}/settings/secrets`
prior to setting up on your airtable api key.


## Client
Contains Airtable integration used in ayon launcher application. Contains publish plugins with logic to integrate editorial return to Airtable.

## Services
Currently, there is `leecher` which stores Airtable webhook events, `processor` which processes to sync data from Airtable to Ayon and `transmitter` which propagates changes from AYON to Airtable. Separation of `leecher` and `processor` allows to restart `processor` without loosing any events that happened meanwhile. The `processer` has nothing to process without running `leecher`. There can be multiple services running at the same time, but they all should be using same version and settings variant.
Both `processor` and `transmitter` need to be run with the Airtable under circumstances, otherwise they would not sync correctly.

1. `Status` fields option needs to align with Project Status options in Ayon
2. `Types` fields option needs to be align with the Tasktypes in Ayon
```
Generic, Art, Modeling, Texture, Lookdev, Rigging, Edit, Layout, Setdress, Animation, Fx, Lighting, Paint, Compositing, Roto, Matchmove
```

## Create package
To create a "server-ready" package of the `server` folder, on a terminal, run `python create_package.py`. That will create `./package/airtable {version}.zip` file that can be uploaded to the server.

## Services
As mentioned there are 3 services `leecher`, `processor` and `transmitter`. These services have docker images that can be started from AYON server. For that there must be running a docker worker called ASH (AYON service host). Once ASH is running you can run services from AYON web UI. This is recommended approach how to run services in production.

To run services locally (recommended only for development purposes), there are 2 possible approaches. One is by running docker image, or using prepared service tools.

- `leecher` - Service that listens to Airtable events and stores them in the AYON database.
- `processor` - Service that is processing Airtable events stored in the AYON database. Only one event is processed at a time.
- `transmitter` - Service that is processing Ayon events and sync the relevant data to Airtable.
