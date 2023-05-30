# os2mo-os2sync-export

Exports from OS2mo to FK-org via OS2Sync
For documentatio on usage and configuration see https://rammearkitektur.docs.magenta.dk/os2mo/data-import-export/exporters/os2sync.html

## Development

When developing you should have a running instance of os2mo available. To start the os2sync-export service run:

```docker-compose up -d --build```

Alternatively, if developing with VSCode, use the launch configs supplied in the repository by pushing the `F5` button.  This allows the use of breakpoints in the editor.

## Tests
The tests can be started using: ```poetry run pytest```
