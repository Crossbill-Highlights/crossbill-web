# Crossbill Anki Plugin

Import flash card questions from Crossbill to Anki.

## Installation

Follow installation instructions on [Anki addon page](https://ankiweb.net/shared/info/1205712943)

## Configuration

### Initial Setup

1. In Anki, go to **Tools → Crossbill Settings**
2. Enter your Crossbill server URL (e.g., `http://localhost:8000`)
3. Click **Test Connection** to verify it works
4. Click **Save**

See [config.md](config.md) for detailed configuration documentation.

## Prerequisites

### Crossbill Server

You need a running Crossbill server with highlights. The server must be accessible from your computer where Anki is installed.

````

## Development

### Setup

This plugin uses Poetry for dependency management and code quality tools.

```bash
cd clients/anki-plugin

# Install dependencies (creates .venv in project directory)
poetry install

# Run code quality checks
poetry run ruff format --check .  # Check formatting
poetry run ruff format .          # Auto-format
poetry run ruff check .           # Lint
poetry run ruff check --fix .     # Auto-fix lint issues
poetry run pyright                # Type checking
````

### Install local version to Anki

1. Clone or download the Crossbill repository

2. Locate your Anki add-ons directory:
   - **Windows**: `%APPDATA%\Anki2\addons21\`
   - **Mac**: `~/Library/Application Support/Anki2/addons21/`
   - **Linux**: `~/.local/share/Anki2/addons21/`

3. Create a symbolic link or copy the plugin folder:

   ```bash
   # Option 1: Symbolic link (recommended for development)
   ln -s /path/to/Crossbill/clients/anki-plugin /path/to/Anki2/addons21/crossbill

   # Option 2: Copy the folder
   cp -r /path/to/Crossbill/clients/anki-plugin /path/to/Anki2/addons21/crossbill

   ```

4. Restart Anki

5. The plugin should appear in Tools → Add-ons

   ```

   ```

### Testing

1. Make changes to the plugin code
2. Restart Anki to reload the plugin
3. Test functionality through the UI
4. Check Anki's console for error messages (Tools → Add-ons → View Files)

### Debugging

Enable Anki's debug console:

1. Help → About → Copy Debug Info (to see Python version and Anki version)
2. Tools → Add-ons → [Select Crossbill] → View Files (to see plugin directory)
3. Check `~/.local/share/Anki2/addons21/crossbill/` for log files

## Contributing

Contributions are welcome! Please see the main [Crossbill repository](https://github.com/Tumetsu/Crossbill) for contribution guidelines.

## License

See the main Crossbill repository for details.

## Support

For issues and feature requests, please visit the [Crossbill repository](https://github.com/Tumetsu/Crossbill/issues).

## Acknowledgments

- Built for [Anki](https://apps.ankiweb.net/), the powerful spaced repetition software
- Part of the [Crossbill](https://github.com/Tumetsu/Crossbill) project
