# Airtable Leecher

The Airtable leecher depends on the [Airtable Addon for AYON](https://github.com/ynput/ayon-airtable) since it expects certain settings provided once the addon is installed in the server.

To get started, create a copy of the `sample_env` file and rename it to `.env` and set the values accordingly, after that you can run the service by issuing:
```sh
make dev
```

Make sure to take a look at the `Makefile` to see what is happening under the hood.
