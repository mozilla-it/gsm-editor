# gsm-editor

A script for editing Google Secret Manager Secrets in a manner consistent with our intended External Secrets usage

### Secret Names

The naming pattern is: `{env}-[{region}-]-gke-{secret}-secrets`

* `region` is optional
* `secret` defaults to `app`

### Examples

#### list revisions of moz-fx-testapp1-nonprod's app secrets for the stage env:

```bash
$ python gsm.py list -p moz-fx-testapp1-nonprod -e stage
```

#### view latest revision of moz-fx-testapp1-nonprod's app secrets for the stage env:

```bash
$ python gsm.py view -p moz-fx-testapp1-nonprod -e stage
```

#### view latest revision of moz-fx-testapp1-nonprod's cronjob-sync-something secrets for the stage env:

```bash
$ python gsm.py view -p moz-fx-testapp1-nonprod -e stage -s cronjob-sync-something
```

#### view latest revision of moz-fx-testapp1-nonprod's app secrets for the stage env in region europe-west1:

```bash
$ python gsm.py view -p moz-fx-testapp1-nonprod -e stage -r europe-west1
```

#### edit latest revision of moz-fx-testapp1-nonprod's app secrets for the stage env:

> creates a new secret if one does not already exist

```bash
$ python gsm.py edit -p moz-fx-testapp1-nonprod -e stage
```
