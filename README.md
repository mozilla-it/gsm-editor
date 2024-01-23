# gsm-editor

A script for editing Google Secret Manager Secrets in a manner consistent with our intended External Secrets usage

### Secret Names

The naming pattern is: `{env}-gke-{secret}-secrets`

* `secret` defaults to `app`

### Examples

#### list revisions of moz-fx-testapp1-nonprod's app secrets for the stage env:

```bash
$ python gsm.py list -p moz-fx-testapp1-nonprod -e stage
```

#### list all secret names in moz-fx-test-app1-nonprod for the stage env:
```bash
$ python gsm.py names -p moz-fx-testapp1-nonprod -e stage
```

#### view latest revision of moz-fx-testapp1-nonprod's app secrets for the stage env:

```bash
$ python gsm.py view -p moz-fx-testapp1-nonprod -e stage
```

#### view latest revision of moz-fx-testapp1-nonprod's cronjob-sync-something secrets for the stage env:

```bash
$ python gsm.py view -p moz-fx-testapp1-nonprod -e stage -s cronjob-sync-something
```

#### edit latest revision of moz-fx-testapp1-nonprod's app secrets for the stage env:

> creates a new secret if one does not already exist

```bash
$ python gsm.py edit -p moz-fx-testapp1-nonprod -e stage
```
