import logging

from scruffy import *

from .ducks import *

log = logging.getLogger('main')


def main():
    # Set up the Environment and load the config
    e = Environment(
        # Main user directory in ~/.duckman, create it if it doesn't exist
        dir=Directory('~/.duckman', create=True,
            # Config file inside ~/.duckman, defaults loaded from default.cfg
            # in the duckman package
            config=ConfigFile('config', defaults=File('default.cfg', parent=PackageDirectory())),

            # User plugins directory at ~/.duckman/plugins
            plugins=PluginDirectory('plugins', create=True)
        ),

        # Plugins directory included with the duckman package.
        plugins_dir=PluginDirectory('plugins', parent=PackageDirectory()),

        # Log directory in a location specified in the config file, create it
        # if it doesn't exist
        log_dir=Directory('{config:logging.log_dir}', create=True,
            # Main log file named as per the configuration. A handler will
            # be created for this log file and added to the logger 'main'
            main_log=LogFile('{config:logging.log_file}', logger='main', formatter='standard')
        )
    )

    print("Set up environment in {}".format(e.dir.path))
    print("Logging to {}".format(e.log_dir.main_log.path))

    log.info("=== Start of duckman log ===")

    # Instantiate any plugins that were registered and tell them to do a thing
    for p in e.plugins:
        log.info("Initialising plugin {}".format(p))
        p().do_a_thing()

    # Check our duck preference
    if e.config.duck_pref == 'upright':
        log.warn("User is an upright heathen.")
    elif e.config.duck_pref == 'flat':
        log.info("User is a flat friend *brofist*.")
    elif e.config.duck_pref == 'rubber':
        log.info("User must be dominicgs")
    else:
        log.error("Umm, {} is not a type of duck".format(e.config.duck_pref))


if __name__ == "__main__":
    main()
