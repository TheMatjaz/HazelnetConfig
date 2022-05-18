HzlConfig: generate Hazelnet configurations from a human-readable JSON file
==============================================================================

The [Hazelnet library](https://github.com/TheMatjaz/Hazelnet) can be configured
via binary configuration files with `.hzl` extension or by providing an already
initialised context structure. There is no fun in writing those by hand, so
this small Python package takes a JSON file with the human-readable
configuration of the entire bus (not just one Party!) and generates the
configurations for each Party.


Usage
-----

```bash
python -m hzlconfig YOUR_CONFIG.json
```

The package generates **and overwrites** the configuration files in
the `generated/` directory.

To start using it, you can try generating the configuration files for
the example configuration `example.json`:

```bash
python -m hzlconfig example.json
```

Write your own bus configuration by editing a copy of `example.json`. The field
names are mapping the field names in the context structures of the Hazelnet
Client and Server. Fields that are not specified for some Clients or Groups
fallback to the values provided in the JSON's `default` field.


Testing HzlConfig
-----------------

To run a simple unit-test of the `hzlconfig` package, call:

```bash
python test\testhzlconfig.py
```

This compiles the `example.json` configuration and verifies is equal to a
known-correct generated set of files.
