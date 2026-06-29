# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
# os2mo-os2sync-export

Exports from OS2mo to FK-org via OS2Sync
For documentation on usage and configuration see https://rammearkitektur.docs.magenta.dk/os2mo/data-import-export/exporters/os2sync.html

## Development

When developing you should have a running instance of os2mo available. To start the os2sync-export service run:

```docker-compose up -d --build```

Alternatively, if developing with VSCode, use the launch configs supplied in the repository by pushing the `F5` button.  This allows the use of breakpoints in the editor.

## Tests
Unittests can be started using: ```poetry run pytest -m "not integration_test"```
Integration tests requires a running instance of os2mo, then run it from docker using `docker compose run --rm os2sync_export pytest -m integration_test`.


## Maintenance

Interactions with fk-org happens through the [OS2Sync API](https://www.os2sync.dk/downloads/API%20Documentation.pdf). Common usefull examples are:

`curl localhost:8081/api/user/<uuid>` - Get read a user from fk-org
`curl localhost:8081/api/orgunit/<uuid>` - Get read an orgunit from fk-org

Sometimes it is necessary to delete a user or orgunit from fk-org and sync it again to fix data issues. To delete a user or orgunit, use:

`curl -X DELETE localhost:8081/api/user/<uuid>` - Delete a user from fk-org
`curl -X DELETE localhost:8081/api/orgunit/<uuid>` - Delete an orgunit from fk-org

Check that the deletion was successful by looking through os2syncs logs (which are quiteverbose) or by checking the database for os2sync with mysql. Check the `queue_users` and `success_users` tables.

In some cases os2sync has trouble syncing deleted users. If this happens, try clearing the "success_users" table (or clear the entire dabatase, with `docker compose -f /opt/docker/os2sync_4/docker-compose.yml down -v && docker compose -f /opt/docker/os2sync_4/docker-compose.yml up -d`. The database is just a cache of what has been synced, so clearing it is fine)

Once the user or orgunit is deleted, trigger a new sync with:

```docker exec -it os2sync_export curl -X POST "localhost:8000/trigger/user/<uuid>"```
```docker exec -it os2sync_export curl -X POST "localhost:8000/trigger/orgunit/<uuid>"```
